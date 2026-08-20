from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import httpx


SUPPORTED_FORMATS = {'.stl': 'model/stl', '.ply': 'application/octet-stream'}
PLATFORMS = {'medit', '3shape', 'exocad', 'itero', 'generic'}
IDENTITY_FILENAME = '.abutmentiq-case.json'


@dataclass(frozen=True)
class UploadCandidate:
    mesh_path: Path
    upload_filename: str
    content_type: str
    source_sha256: str
    source_event_id: str
    patient_name: str
    clinic_reference: str
    order_reference: str | None
    platform: str
    connector_id: str


@dataclass(frozen=True)
class UploadResult:
    status_code: int
    status: str
    case_code: str | None


@dataclass
class Observation:
    size: int
    mtime_ns: int
    stable_since: float


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(stat.S_IRWXU)
    except OSError:
        pass
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    temporary.chmod(stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temporary, path)


def _read_identity(mesh_path: Path, source_root: Path) -> dict[str, str] | None:
    current = mesh_path.parent.resolve()
    root = source_root.resolve()
    while current == root or root in current.parents:
        metadata_path = current / IDENTITY_FILENAME
        if metadata_path.is_file() and not metadata_path.is_symlink():
            try:
                payload = json.loads(metadata_path.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                return None
            if not isinstance(payload, dict):
                return None
            patient = str(payload.get('patient_name', '')).strip()
            clinic = str(payload.get('clinic_reference', '')).strip()
            order = str(payload.get('order_reference', '')).strip()
            if not patient or not clinic or len(patient) > 200 or len(clinic) > 200 or len(order) > 200:
                return None
            return {
                'patient_name': patient,
                'clinic_reference': clinic,
                'order_reference': order,
            }
        if current == root:
            break
        current = current.parent
    return None


class FolderBridge:
    """Observa una exportación autorizada en solo lectura y envía mallas estables."""

    def __init__(
        self,
        *,
        source_root: Path | str,
        state_path: Path | str,
        platform: str,
        connector_id: str,
        stable_window_seconds: int = 30,
        sender: Callable[[UploadCandidate], UploadResult],
        max_mesh_bytes: int = 100 * 1024 * 1024,
        max_candidates: int = 1000,
    ) -> None:
        self.source_root = Path(source_root).resolve()
        self.state_path = Path(state_path)
        self.platform = platform.casefold()
        self.connector_id = connector_id
        self.stable_window_seconds = max(0, int(stable_window_seconds))
        self.max_mesh_bytes = max(1, int(max_mesh_bytes))
        self.max_candidates = max(1, int(max_candidates))
        self.sender = sender
        self.observations: dict[Path, Observation] = {}
        if self.platform not in PLATFORMS:
            raise ValueError('Plataforma no admitida')
        if re.fullmatch(r'[A-Za-z0-9._:-]{2,80}', connector_id) is None:
            raise ValueError('connector_id no válido')
        if not self.source_root.is_dir():
            raise ValueError('La carpeta de origen no existe')
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {'schema_version': 1, 'processed': {}}
        payload = json.loads(self.state_path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or not isinstance(payload.get('processed'), dict):
            raise ValueError('Estado del puente no válido')
        return payload

    def _save_processed(self, source_sha256: str, status: str, case_code: str | None) -> None:
        self.state['processed'][source_sha256] = {
            'status': status,
            'case_code': case_code,
            'recorded_at_unix': int(time.time()),
        }
        _atomic_json_write(self.state_path, self.state)

    def _discover(self) -> list[Path]:
        paths: list[Path] = []
        for path in self.source_root.rglob('*'):
            if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in SUPPORTED_FORMATS:
                continue
            try:
                resolved = path.resolve(strict=True)
            except OSError:
                continue
            if self.source_root != resolved.parent and self.source_root not in resolved.parents:
                continue
            paths.append(resolved)
            if len(paths) >= self.max_candidates:
                break
        return sorted(paths, key=lambda item: item.as_posix())

    def run_once(self, *, now: float | None = None) -> list[dict[str, str | None]]:
        observed_at = time.monotonic() if now is None else float(now)
        events: list[dict[str, str | None]] = []
        present: set[Path] = set()
        for mesh_path in self._discover():
            present.add(mesh_path)
            try:
                file_stat = mesh_path.stat()
            except OSError:
                continue
            signature = (file_stat.st_size, file_stat.st_mtime_ns)
            if file_stat.st_size > self.max_mesh_bytes:
                events.append({'status': 'QUARANTINED_SIZE_LIMIT', 'case_code': None})
                continue
            prior = self.observations.get(mesh_path)
            if prior is None or (prior.size, prior.mtime_ns) != signature:
                self.observations[mesh_path] = Observation(*signature, stable_since=observed_at)
                if self.stable_window_seconds > 0:
                    continue
            observation = self.observations[mesh_path]
            if observed_at - observation.stable_since < self.stable_window_seconds:
                continue

            try:
                source_sha256 = _sha256_file(mesh_path)
            except OSError:
                continue
            if source_sha256 in self.state['processed']:
                continue
            identity = _read_identity(mesh_path, self.source_root)
            if identity is None:
                events.append({'status': 'QUARANTINED_IDENTITY_REQUIRED', 'case_code': None})
                continue

            extension = mesh_path.suffix.casefold()
            candidate = UploadCandidate(
                mesh_path=mesh_path,
                upload_filename=f'mesh{extension}',
                content_type=SUPPORTED_FORMATS[extension],
                source_sha256=source_sha256,
                source_event_id=f'BRIDGE-{source_sha256[:24].upper()}',
                patient_name=identity['patient_name'],
                clinic_reference=identity['clinic_reference'],
                order_reference=identity['order_reference'] or None,
                platform=self.platform,
                connector_id=self.connector_id,
            )
            result = self.sender(candidate)
            if result.status_code in {200, 201}:
                final_status = result.status
                self._save_processed(source_sha256, final_status, result.case_code)
            elif result.status_code == 409 and result.status == 'DUPLICATE_GEOMETRY':
                final_status = 'QUARANTINED_DUPLICATE_GEOMETRY'
                self._save_processed(source_sha256, final_status, None)
            elif result.status_code in {413, 415, 422}:
                final_status = 'QUARANTINED_SERVER_REJECTED'
                self._save_processed(source_sha256, final_status, None)
            else:
                final_status = 'RETRY_REQUIRED'
            events.append({'status': final_status, 'case_code': result.case_code})

        for path in set(self.observations) - present:
            self.observations.pop(path, None)
        return events


def http_sender(api_base: str, token: str, timeout_seconds: float = 120.0) -> Callable[[UploadCandidate], UploadResult]:
    parsed = urlsplit(api_base)
    localhost_http = parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'}
    if parsed.scheme != 'https' and not localhost_http:
        raise ValueError('La API debe usar HTTPS salvo localhost')
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('La URL de API no puede contener credenciales, query ni fragmento')
    endpoint = f"{api_base.rstrip('/')}/api/platform-intake/mesh"

    def send(candidate: UploadCandidate) -> UploadResult:
        data = {
            'platform': candidate.platform,
            'connector_id': candidate.connector_id,
            'source_event_id': candidate.source_event_id,
            'patient_name': candidate.patient_name,
            'clinic_reference': candidate.clinic_reference,
        }
        if candidate.order_reference:
            data['order_reference'] = candidate.order_reference
        with candidate.mesh_path.open('rb') as stream:
            response = httpx.post(
                endpoint,
                headers={'Authorization': f'Bearer {token}'},
                data=data,
                files={'mesh': (candidate.upload_filename, stream, candidate.content_type)},
                timeout=timeout_seconds,
                follow_redirects=False,
            )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code in {200, 201}:
            case = payload.get('case') if isinstance(payload, dict) else None
            return UploadResult(response.status_code, str(payload.get('status', 'ENQUEUED')), str(case.get('case_code')) if isinstance(case, dict) else None)
        detail = payload.get('detail', {}) if isinstance(payload, dict) else {}
        code = str(detail.get('code', f'HTTP_{response.status_code}')) if isinstance(detail, dict) else f'HTTP_{response.status_code}'
        if response.status_code in {401, 403}:
            raise RuntimeError('Autenticación del conector rechazada')
        return UploadResult(response.status_code, code, None)

    return send


def main() -> int:
    parser = argparse.ArgumentParser(description='Puente local de solo lectura para AbutmentIQ')
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--state-path', required=True)
    parser.add_argument('--api-base', default=os.environ.get('ABUTMENTIQ_API_BASE'))
    parser.add_argument('--platform', choices=sorted(PLATFORMS), default='generic')
    parser.add_argument('--connector-id', required=True)
    parser.add_argument('--stable-seconds', type=int, default=30)
    parser.add_argument('--poll-seconds', type=int, default=5)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    token = os.environ.get('ABUTMENTIQ_PLATFORM_INGEST_TOKEN')
    if not args.api_base or not token:
        parser.error('ABUTMENTIQ_API_BASE/--api-base y ABUTMENTIQ_PLATFORM_INGEST_TOKEN son obligatorios')
    bridge = FolderBridge(
        source_root=args.source_root,
        state_path=args.state_path,
        platform=args.platform,
        connector_id=args.connector_id,
        stable_window_seconds=args.stable_seconds,
        sender=http_sender(args.api_base, token),
    )
    while True:
        try:
            for event in bridge.run_once():
                print(json.dumps(event, sort_keys=True), flush=True)
        except (OSError, ValueError, httpx.HTTPError, RuntimeError) as exc:
            print(json.dumps({'status': 'BRIDGE_ERROR_RETRY', 'error_type': type(exc).__name__}), file=sys.stderr, flush=True)
        if args.once:
            return 0
        time.sleep(max(1, args.poll_seconds))


if __name__ == '__main__':
    raise SystemExit(main())
