from __future__ import annotations

import base64
import fcntl
import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Callable, Literal
from urllib.parse import urlsplit

import joblib
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .agent_service import compose_assessment, record_feedback
from .identity_vault import load_private_identity, store_private_identity, validate_identity_key
from .mesh_features import mesh_features
from .platform_intake import geometry_sha256, scan_read_only_connectors


class AnalyzeRequest(BaseModel):
    functional_class: str = Field(min_length=2, max_length=120)
    question: str = Field(default="calidad técnica scanbody escaneado implantes", max_length=500)


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: str
    human_label: Literal["CORRECTA", "CONDICIONAL", "INCORRECTA", "NO_EVALUABLE"]
    judgment: Literal["CORRECT", "INCORRECT"]
    notes: str = Field(default="", max_length=4000)
    functional_class: str = Field(min_length=2, max_length=120)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_mesh_features(pipeline_path: Path):
    spec = importlib.util.spec_from_file_location("abutmentiq_training_pipeline", pipeline_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el pipeline: {pipeline_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.mesh_features


def _rag_search(db_path: Path, query: str, limit: int = 4) -> list[dict[str, Any]]:
    import re

    terms = [term for term in re.findall(r"\w+", query.casefold()) if len(term) > 2]
    if not terms:
        terms = ["scanbody", "implantes", "escaneado"]
    fts_query = " OR ".join(f'"{term}"' for term in terms[:16])
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            """SELECT f.text,f.ordinal,d.title,d.confidence,d.sha256,bm25(chunks_fts) AS rank
               FROM chunks_fts f JOIN documents d ON d.id=f.document_id
               WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?""",
            (fts_query, max(limit * 8, 20)),
        ).fetchall()
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if row["sha256"] in seen:
            continue
        seen.add(row["sha256"])
        output.append({
            "title": row["title"],
            "text": row["text"],
            "confidence": row["confidence"],
            "document_sha256": row["sha256"],
            "ordinal": int(row["ordinal"]),
        })
        if len(output) >= limit:
            break
    return output


def _read_jsonl_bounded(
    path: Path,
    *,
    max_bytes: int = 64 * 1024 * 1024,
    max_records: int = 100_000,
    max_line_bytes: int = 64 * 1024,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.stat().st_size > max_bytes:
        raise ValueError(f"Registro persistente excede {max_bytes} bytes")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            if len(line.encode("utf-8")) > max_line_bytes:
                raise ValueError("Evento persistente demasiado grande")
            records.append(json.loads(line))
            if len(records) > max_records:
                raise ValueError("Demasiados eventos persistentes")
    return records


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _append_jsonl_locked(path: Path, payload: dict[str, Any], *, unique_key: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        for line in handle:
            if line.strip() and json.loads(line).get(unique_key) == payload.get(unique_key):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                return False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return True


def create_app(
    *,
    runtime_dir: Path | str,
    demo_mesh: Path | str,
    model_path: Path | str,
    benchmark_path: Path | str,
    manifest_path: Path | str,
    knowledge_db: Path | str,
    demo_source_sha256: str | None = None,
    daily_state_path: Path | str | None = None,
    daily_outgoing_root: Path | str | None = None,
    daily_history_path: Path | str | None = None,
    daily_advance_callback: Callable[[], None] | None = None,
    platform_connectors_path: Path | str | None = None,
    platform_ingest_token: str | None = None,
    platform_ingest_max_bytes: int = 100 * 1024 * 1024,
    identity_encryption_key: str | None = None,
    static_dir: Path | str | None = None,
    app_auth_username: str | None = None,
    app_auth_password: str | None = None,
    allowed_origins: tuple[str, ...] | None = None,
    before_json_write: Callable[[Path], None] | None = None,
) -> FastAPI:
    runtime = Path(runtime_dir)
    runtime.mkdir(parents=True, exist_ok=True)
    if identity_encryption_key is not None:
        validate_identity_key(identity_encryption_key)
    if bool(app_auth_username) != bool(app_auth_password):
        raise ValueError("Usuario y contraseña de aplicación deben configurarse juntos")
    if app_auth_password is not None and len(app_auth_password) < 14:
        raise ValueError("La contraseña de aplicación debe tener al menos 14 caracteres")
    normalized_origins: set[str] = set()
    for origin in allowed_origins or ():
        parsed_origin = urlsplit(origin.strip())
        if (
            parsed_origin.scheme not in {"http", "https"}
            or not parsed_origin.netloc
            or parsed_origin.username
            or parsed_origin.password
            or parsed_origin.path not in {"", "/"}
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise ValueError("Origen permitido no válido")
        normalized_origins.add(f"{parsed_origin.scheme.casefold()}://{parsed_origin.netloc.casefold()}")
    private_identity_path = runtime / "private_identities.jsonl"
    static_root = Path(static_dir).resolve() if static_dir is not None else None
    mesh_path = Path(demo_mesh)
    if demo_source_sha256 is None:
        demo_source_sha256 = _sha256_file(mesh_path)
    model_file = Path(model_path)
    benchmark_file = Path(benchmark_path)
    manifest_file = Path(manifest_path)
    local_knowledge = runtime / "knowledge.db"
    if not local_knowledge.exists():
        shutil.copy2(Path(knowledge_db), local_knowledge)

    model = joblib.load(model_file)
    benchmark = json.loads(benchmark_file.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    known_hashes = {str(item["sha256"]) for item in manifest.get("records", [])}
    reviews_path = runtime / "reviews.jsonl"
    if reviews_path.exists():
        try:
            with reviews_path.open("r", encoding="utf-8") as persisted_reviews:
                for line in persisted_reviews:
                    if not line.strip():
                        continue
                    if len(line) > 1_048_576:
                        raise ValueError("Línea de revisión demasiado grande")
                    persisted_review = json.loads(line)
                    source_hash = str(persisted_review.get("source_mesh_sha256", ""))
                    if re.fullmatch(r"[0-9a-f]{64}", source_hash) is None:
                        raise ValueError("Revisión persistida sin SHA-256 válido")
                    known_hashes.add(source_hash)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("El registro persistente de revisiones no es válido") from exc
    assessments_path = runtime / "assessments.jsonl"
    assessments: dict[str, dict[str, Any]] = {}
    if assessments_path.exists():
        try:
            for persisted in _read_jsonl_bounded(assessments_path):
                assessment_id = str(persisted.get("assessment_id", ""))
                if not assessment_id or not persisted.get("case_code") or not persisted.get("source_mesh_sha256"):
                    raise ValueError("Evaluación persistida incompleta")
                assessments[assessment_id] = persisted
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("El registro persistente de evaluaciones no es válido") from exc
    queue_state_path = Path(daily_state_path) if daily_state_path is not None else None
    queue_outgoing_root = Path(daily_outgoing_root).resolve() if daily_outgoing_root is not None else None
    queue_history_path = Path(daily_history_path) if daily_history_path is not None else None
    connectors_config_path = Path(platform_connectors_path) if platform_connectors_path is not None else None

    app = FastAPI(title="AbutmentIQ Supervised Agent", version="0.4.0")
    app.state.assessments = assessments

    @app.middleware("http")
    async def production_access_control(request: Request, call_next):
        if app_auth_username is None or app_auth_password is None:
            return await call_next(request)
        path = request.url.path
        independently_authenticated = path.startswith("/api/platform-intake/")
        if path == "/healthz" or independently_authenticated:
            return await call_next(request)
        authorization = request.headers.get("authorization", "")
        authenticated = False
        if authorization.startswith("Basic "):
            try:
                cleartext = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
                username, password = cleartext.split(":", 1)
                authenticated = secrets.compare_digest(username, app_auth_username) and secrets.compare_digest(password, app_auth_password)
            except (ValueError, UnicodeDecodeError):
                authenticated = False
        if not authenticated:
            return JSONResponse(
                status_code=401,
                content={"detail": {"code": "APP_AUTH_REQUIRED", "message": "Autenticación requerida"}},
                headers={"WWW-Authenticate": 'Basic realm="AbutmentIQ"'},
            )
        request.state.authenticated_username = app_auth_username
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            parsed_request_origin = urlsplit(origin) if origin else None
            normalized_request_origin = (
                f"{parsed_request_origin.scheme.casefold()}://{parsed_request_origin.netloc.casefold()}"
                if parsed_request_origin and parsed_request_origin.scheme and parsed_request_origin.netloc else ""
            )
            request_host = request.headers.get("host", "").casefold()
            same_host_fallback = bool(parsed_request_origin) and parsed_request_origin.netloc.casefold() == request_host
            origin_allowed = (
                normalized_request_origin in normalized_origins
                if normalized_origins else same_host_fallback
            )
            if not origin_allowed:
                return JSONResponse(
                    status_code=403,
                    content={"detail": {"code": "INVALID_REQUEST_ORIGIN", "message": "Origen de escritura no autorizado"}},
                )
        return await call_next(request)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    def load_platform_connectors() -> list[dict[str, Any]]:
        if connectors_config_path is None or not connectors_config_path.exists():
            return []
        try:
            payload = json.loads(connectors_config_path.read_text(encoding="utf-8"))
            connectors = payload.get("connectors", [])
            if not isinstance(connectors, list):
                raise ValueError("connectors debe ser una lista")
            return [item for item in connectors if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(503, "Configuración de plataformas no disponible") from exc

    def resolve_prepared_case(prepared: dict[str, Any]) -> dict[str, Any] | None:
        if queue_outgoing_root is None:
            return None
        case_code = str(prepared.get("case_code", ""))
        if re.fullmatch(r"AIQ-[A-Z0-9-]{4,64}", case_code) is None:
            return None
        case_dirs = sorted(
            (path for path in queue_outgoing_root.glob(f"*_{case_code}") if path.is_dir()),
            reverse=True,
        )
        mesh_path: Path | None = None
        for case_dir in case_dirs:
            candidates = sorted(
                path for path in case_dir.iterdir()
                if path.is_file() and path.suffix.casefold() in {".stl", ".ply"}
            )
            if candidates:
                mesh_path = candidates[0].resolve()
                break
        if mesh_path is None or not mesh_path.is_relative_to(queue_outgoing_root):
            return None
        delivered_sha = _sha256_file(mesh_path)
        expected_delivered_sha = str(prepared.get("delivered_stl_sha256", delivered_sha))
        if delivered_sha != expected_delivered_sha:
            raise HTTPException(409, f"Integridad de la malla no válida para {case_code}")
        return {
            "case_code": case_code,
            "daily_slot": int(prepared.get("daily_slot", 0)),
            "daily_total": int(prepared.get("daily_total", 0)),
            "review_status": str(prepared.get("review_status", "UNKNOWN")),
            "source_mesh_sha256": str(prepared.get("source_mesh_sha256", "")),
            "mesh_format": mesh_path.suffix.casefold().lstrip("."),
            "mesh_url": f"/api/review-queue/{case_code}/mesh",
            "triangle_count": int(prepared.get("triangle_count", 0)),
            "_mesh_path": mesh_path,
        }

    def resolve_queue_cases() -> list[dict[str, Any]]:
        if queue_state_path is None or queue_outgoing_root is None or not queue_state_path.exists():
            return []
        try:
            state = json.loads(queue_state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(503, "La cola diaria no está disponible") from exc
        cases: list[dict[str, Any]] = []
        for prepared in state.get("prepared", []):
            if str(prepared.get("queue_visibility", "ACTIVE")) == "PENDING":
                continue
            case = resolve_prepared_case(prepared)
            if case is not None:
                cases.append(case)
        return cases

    def public_queue_case(case: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "case_code", "daily_slot", "daily_total", "review_status",
            "mesh_format", "mesh_url", "triangle_count", "origin_platform",
        }
        return {key: case[key] for key in allowed if key in case}

    def public_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "schema_version", "assessment_id", "case_code", "created_at", "decision_status",
            "clinical_decision", "requires_human_confirmation", "agent_output", "technical_features",
            "training", "functional_class", "question", "original_filename_stored", "queue_source",
        }
        payload = {key: assessment[key] for key in allowed if key in assessment}
        rag = assessment.get("rag", {})
        payload["rag"] = {
            "status": rag.get("status", "SIN_EVIDENCIA_RECUPERADA"),
            "clinical_ground_truth": bool(rag.get("clinical_ground_truth", False)),
            "citations": [
                {key: citation[key] for key in ("title", "text", "confidence", "ordinal") if key in citation}
                for citation in rag.get("citations", [])
            ],
        }
        return payload

    def public_review(review: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "review_id", "assessment_id", "case_code", "human_label",
            "agent_was_correct", "training_eligibility", "new_training_sample",
            "previous_system_output", "functional_class", "timestamp",
            "candidate_event_added", "queue_status_updated",
        }
        return {key: review[key] for key in allowed if key in review}

    def queue_case(case_code: str) -> dict[str, Any]:
        case = next((item for item in resolve_queue_cases() if item["case_code"] == case_code), None)
        if case is None:
            raise HTTPException(404, "Caso no encontrado en la cola diaria")
        return case

    workflow_lock_path = runtime / "workflow.lock"

    def mark_queue_case_completed(case_code: str, app_review_id: str, reviewed_at: str) -> bool:
        if queue_state_path is None or not queue_state_path.exists():
            return False

        def updated_payload(path: Path, *, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise HTTPException(503, "Estado operativo de cola no disponible") from exc
            elif fallback is not None:
                payload = json.loads(json.dumps(fallback))
            else:
                raise HTTPException(503, "Estado operativo de cola no disponible")
            matched = False
            for item in payload.get("prepared", []):
                if str(item.get("case_code")) != case_code:
                    continue
                matched = True
                prior_review_id = str(item.get("app_review_id", ""))
                if item.get("review_status") == "COMPLETED" and prior_review_id not in {"", app_review_id}:
                    raise HTTPException(409, "El caso ya fue completado por otra revisión")
                item["review_status"] = "COMPLETED"
                item["app_review_id"] = app_review_id
                item["reviewed_at"] = reviewed_at
            if not matched:
                raise HTTPException(404, "Caso diario no encontrado en el estado operativo")
            return payload

        with workflow_lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            state_payload = updated_payload(queue_state_path)
            history_payload = (
                updated_payload(queue_history_path, fallback=state_payload)
                if queue_history_path is not None else None
            )
            atomic_json_write(queue_state_path, state_payload)
            if queue_history_path is not None and history_payload is not None:
                atomic_json_write(queue_history_path, history_payload)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return True

    @app.get("/api/status")
    def status():
        with sqlite3.connect(local_knowledge) as db:
            documents = int(db.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
            chunks = int(db.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0])
        return {
            "status": "ok",
            "mode": "local-first-supervised",
            "clinical_autonomy": False,
            "rag": {"documents": documents, "chunks": chunks},
            "model": {"version": benchmark.get("model_version", benchmark.get("run_id", "unknown")), "promotion": "NO_PROMOTION"},
        }

    async def persist_platform_upload(upload: UploadFile) -> tuple[Path, str]:
        suffix = Path(upload.filename or "").suffix.casefold()
        if suffix not in {".stl", ".ply"}:
            raise HTTPException(415, {"code": "UNSUPPORTED_MESH_FORMAT", "message": "Solo se admiten STL y PLY"})
        staging = runtime / "platform-staging"
        staging.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix="incoming-", suffix=suffix, dir=staging)
        digest = hashlib.sha256()
        total = 0
        try:
            with os.fdopen(fd, "wb") as handle:
                while chunk := await upload.read(4 * 1024 * 1024):
                    total += len(chunk)
                    if total > platform_ingest_max_bytes:
                        raise HTTPException(413, {"code": "MESH_TOO_LARGE", "message": "La malla supera el límite configurado"})
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            if total == 0:
                raise HTTPException(422, {"code": "EMPTY_MESH", "message": "La malla está vacía"})
            return Path(temporary_name), digest.hexdigest()
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
        if before_json_write is not None:
            before_json_write(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    def private_reference_commitment(*, domain: str, value: str) -> str:
        if identity_encryption_key is None:
            raise RuntimeError("La clave de identidad no está configurada")
        commitment_key = hashlib.sha256(
            identity_encryption_key.encode("ascii") + b"\0abutmentiq-private-reference-v1"
        ).digest()
        message = domain.encode("ascii") + b"\0" + value.encode("utf-8")
        return hmac.new(commitment_key, message, hashlib.sha256).hexdigest()

    def identity_commitment(*, patient: str, clinic: str, order: str, event: str) -> str:
        normalized = json.dumps({
            "patient_name": patient.strip(),
            "clinic_reference": clinic.strip(),
            "order_reference": order.strip(),
            "source_event_id": event.strip(),
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return private_reference_commitment(
            domain="ingest-identity-v1", value=normalized.decode("utf-8"),
        )

    @app.post("/api/platform-intake/mesh", status_code=201)
    async def ingest_platform_mesh(
        response: Response,
        platform: Annotated[str, Form(min_length=2, max_length=32)],
        connector_id: Annotated[str, Form(min_length=3, max_length=64)],
        mesh: Annotated[UploadFile, File()],
        source_event_id: Annotated[str, Form(max_length=256)] = "",
        patient_name: Annotated[str, Form(max_length=200)] = "",
        clinic_reference: Annotated[str, Form(max_length=200)] = "",
        order_reference: Annotated[str, Form(max_length=200)] = "",
        authorization: str | None = Header(default=None),
    ):
        if not platform_ingest_token:
            raise HTTPException(503, {"code": "PLATFORM_INGEST_NOT_CONFIGURED", "message": "La ingesta de plataformas no está configurada"})
        expected_authorization = f"Bearer {platform_ingest_token}"
        if authorization is None or not secrets.compare_digest(authorization, expected_authorization):
            raise HTTPException(401, {"code": "INVALID_PLATFORM_TOKEN", "message": "Autenticación de plataforma requerida"}, headers={"WWW-Authenticate": "Bearer"})
        if not patient_name.strip() or not clinic_reference.strip():
            raise HTTPException(422, {"code": "PRIVATE_IDENTITY_REQUIRED", "message": "Paciente y clínica son obligatorios"})
        if not source_event_id.strip():
            raise HTTPException(422, {"code": "SOURCE_EVENT_REQUIRED", "message": "El identificador de evento de origen es obligatorio"})
        if identity_encryption_key is None:
            raise HTTPException(503, {"code": "IDENTITY_VAULT_NOT_CONFIGURED", "message": "La bóveda de identidad no está configurada"})
        platform_id = platform.casefold().strip()
        source_event_id = source_event_id.strip()
        if platform_id not in {"medit", "3shape", "exocad", "itero", "generic"}:
            raise HTTPException(422, {"code": "UNSUPPORTED_PLATFORM", "message": "Plataforma no soportada"})
        if re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", connector_id) is None:
            raise HTTPException(422, {"code": "INVALID_CONNECTOR_ID", "message": "Identificador de conector no válido"})
        if queue_state_path is None or queue_outgoing_root is None:
            raise HTTPException(503, {"code": "REVIEW_QUEUE_NOT_CONFIGURED", "message": "La cola de revisión no está configurada"})

        temporary_path, source_sha = await persist_platform_upload(mesh)
        try:
            try:
                geometry_sha = geometry_sha256(temporary_path)
                features = mesh_features(temporary_path)
            except Exception as exc:
                raise HTTPException(422, {"code": "INVALID_MESH", "message": "La geometría STL/PLY no es válida"}) from exc

            queue_outgoing_root.mkdir(parents=True, exist_ok=True)
            lock_path = workflow_lock_path
            with lock_path.open("a+", encoding="utf-8") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                if queue_state_path.exists():
                    state = json.loads(queue_state_path.read_text(encoding="utf-8"))
                else:
                    state = {"schema_version": 2, "prepared": []}
                prepared = state.setdefault("prepared", [])
                source_event_sha = private_reference_commitment(
                    domain="source-event-id-v1", value=source_event_id,
                )
                request_identity_commitment = identity_commitment(
                    patient=patient_name, clinic=clinic_reference,
                    order=order_reference, event=source_event_id,
                )
                event_key_commitment = private_reference_commitment(
                    domain="source-event-key-v1",
                    value=f"{platform_id}|{connector_id}|{source_event_id}",
                )
                operations_path = runtime / "ingest_operations.jsonl"
                operations = _read_jsonl_bounded(operations_path)
                existing_operation = next((
                    item for item in operations if item.get("event_key_commitment") == event_key_commitment
                ), None)
                if existing_operation is not None and existing_operation.get("source_mesh_sha256") != source_sha:
                    raise HTTPException(409, {
                        "code": "SOURCE_EVENT_CONFLICT",
                        "message": "El evento de origen ya fue recibido con otro contenido; se requiere revisión manual",
                    })
                if existing_operation is not None and not secrets.compare_digest(
                    str(existing_operation.get("identity_commitment", "")), request_identity_commitment,
                ):
                    raise HTTPException(409, {
                        "code": "SOURCE_IDENTITY_CONFLICT",
                        "message": "El evento preparado está vinculado a otra identidad privada",
                    })
                existing_event = next((
                    item for item in prepared
                    if item.get("origin_platform") == platform_id
                    and item.get("connector_id") == connector_id
                    and item.get("source_event_id_commitment") == source_event_sha
                ), None)
                if existing_event is not None and existing_event.get("source_mesh_sha256") != source_sha:
                    raise HTTPException(409, {
                        "code": "SOURCE_EVENT_CONFLICT",
                        "message": "El evento de origen ya fue recibido con otro contenido; se requiere revisión manual",
                    })
                existing_source = next((
                    item for item in prepared
                    if item.get("source_mesh_sha256") == source_sha
                ), None)
                if existing_source is not None:
                    case_code = str(existing_source["case_code"])
                    existing_identity = load_private_identity(
                        path=private_identity_path,
                        encryption_key=identity_encryption_key,
                        case_code=case_code,
                    )
                    expected_identity = {
                        "patient_name": patient_name.strip(),
                        "clinic_reference": clinic_reference.strip(),
                        "order_reference": order_reference.strip(),
                        "source_event_id": source_event_id.strip(),
                    }
                    if existing_identity is None:
                        store_private_identity(
                            path=private_identity_path,
                            encryption_key=identity_encryption_key,
                            case_code=case_code,
                            patient_name=patient_name,
                            clinic_reference=clinic_reference,
                            order_reference=order_reference,
                            source_event_id=source_event_id,
                            created_at=str(existing_source.get("received_at", _utc_now())),
                        )
                        existing_identity = load_private_identity(
                            path=private_identity_path,
                            encryption_key=identity_encryption_key,
                            case_code=case_code,
                        )
                    identity_matches = existing_identity is not None and all(
                        secrets.compare_digest(
                            str(existing_identity.get(field, "")).encode("utf-8"),
                            expected.encode("utf-8"),
                        )
                        for field, expected in expected_identity.items()
                    ) and existing_source.get("origin_platform") == platform_id \
                        and existing_source.get("connector_id") == connector_id
                    if not identity_matches:
                        _append_jsonl_locked(runtime / "identity_conflicts.jsonl", {
                            "schema_version": 1,
                            "event_id": secrets.token_hex(16),
                            "event_type": "SOURCE_IDENTITY_CONFLICT_BLOCKED",
                            "case_code": case_code,
                            "platform": platform_id,
                            "connector_id": connector_id,
                            "received_at": _utc_now(),
                        }, unique_key="event_id")
                        raise HTTPException(409, {
                            "code": "SOURCE_IDENTITY_CONFLICT",
                            "message": "La fuente ya existe vinculada a otra identidad privada; se requiere revisión manual",
                        })
                    received_at = str(existing_source.get("received_at", _utc_now()))
                    slot = int(existing_source.get("daily_slot", 0))
                    matching_dirs = sorted(
                        path for path in queue_outgoing_root.glob(f"*_{case_code}") if path.is_dir()
                    )
                    case_dir = matching_dirs[-1] if matching_dirs else (
                        queue_outgoing_root / f"{received_at[:10]}_{slot:04d}_{case_code}"
                    )
                    case_dir.mkdir(parents=True, exist_ok=True)
                    mesh_candidates = sorted(
                        path for path in case_dir.iterdir()
                        if path.is_file() and path.suffix.casefold() in {".stl", ".ply"}
                    )
                    if mesh_candidates:
                        if _sha256_file(mesh_candidates[0]) != source_sha:
                            raise HTTPException(409, {
                                "code": "INGEST_RECOVERY_MESH_CONFLICT",
                                "message": "El artefacto de malla requiere recuperación manual",
                            })
                    else:
                        repaired_mesh = case_dir / f"mesh{temporary_path.suffix.casefold()}"
                        shutil.copyfile(temporary_path, repaired_mesh)
                        existing_source["delivered_stl_sha256"] = _sha256_file(repaired_mesh)
                        atomic_json_write(queue_state_path, state)

                    if queue_history_path is not None:
                        if queue_history_path.exists():
                            history = json.loads(queue_history_path.read_text(encoding="utf-8"))
                        else:
                            history = {"schema_version": 2, "prepared": []}
                        history_records = history.setdefault("prepared", [])
                        if not any(item.get("case_code") == case_code for item in history_records):
                            history_records.append(dict(existing_source))
                            atomic_json_write(queue_history_path, history)

                    intake_event = {
                        "schema_version": 1,
                        "event_type": "AUTHENTICATED_PLATFORM_INGEST",
                        "case_code": case_code,
                        "platform": str(existing_source.get("origin_platform", platform_id)),
                        "connector_id": str(existing_source.get("connector_id", connector_id)),
                        "source_sha256": source_sha,
                        "geometry_sha256": str(existing_source.get("geometry_sha256", geometry_sha)),
                        "source_event_id_commitment": existing_source.get("source_event_id_commitment"),
                        "original_filename_stored": False,
                        "received_at": received_at,
                    }
                    _append_jsonl_locked(
                        runtime / "platform_intake.jsonl", intake_event, unique_key="source_sha256"
                    )
                    response.status_code = 200
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                    case = resolve_prepared_case(existing_source)
                    if case is None:
                        raise HTTPException(409, {"code": "QUEUE_CASE_MISSING", "message": "El caso idempotente no está disponible"})
                    return {
                        "status": "ALREADY_ENQUEUED",
                        "duplicate_reason": "SOURCE_SHA256",
                        "case": public_queue_case(case),
                    }
                existing_geometry = next((
                    item for item in prepared
                    if item.get("geometry_sha256") == geometry_sha
                ), None)
                if existing_geometry is not None:
                    duplicate_event = {
                        "schema_version": 1,
                        "event_type": "DUPLICATE_GEOMETRY_QUARANTINED",
                        "platform": platform_id,
                        "connector_id": connector_id,
                        "source_sha256": source_sha,
                        "geometry_sha256": geometry_sha,
                        "source_event_id_commitment": source_event_sha,
                        "original_filename_stored": False,
                        "received_at": _utc_now(),
                    }
                    _append_jsonl_locked(runtime / "platform_intake.jsonl", duplicate_event, unique_key="source_sha256")
                    raise HTTPException(409, {
                        "code": "DUPLICATE_GEOMETRY",
                        "message": "La geometría ya fue recibida con otro archivo; se ha bloqueado para revisión",
                    })

                if existing_operation is not None:
                    slot = int(existing_operation["daily_slot"])
                    case_code = str(existing_operation["case_code"])
                    received_at = str(existing_operation["received_at"])
                else:
                    slot = max((int(item.get("daily_slot", 0)) for item in prepared), default=0) + 1
                    case_code = f"AIQ-{secrets.token_hex(8).upper()}"
                    received_at = _utc_now()
                    _append_jsonl_locked(operations_path, {
                        "schema_version": 1,
                        "event_key_commitment": event_key_commitment,
                        "platform": platform_id,
                        "connector_id": connector_id,
                        "source_event_id_commitment": source_event_sha,
                        "source_mesh_sha256": source_sha,
                        "geometry_sha256": geometry_sha,
                        "identity_commitment": request_identity_commitment,
                        "case_code": case_code,
                        "daily_slot": slot,
                        "received_at": received_at,
                        "status": "PREPARED",
                    }, unique_key="event_key_commitment")
                if existing_operation is None:
                    orphaned_identity = load_private_identity(
                        path=private_identity_path,
                        encryption_key=identity_encryption_key,
                        case_code=case_code,
                    )
                    if orphaned_identity is not None:
                        raise HTTPException(409, {
                            "code": "ORPHANED_PRIVATE_IDENTITY_RECOVERY_REQUIRED",
                            "message": "Existe una identidad privada sin estado operativo; se requiere recuperación manual",
                        })
                case_dir = queue_outgoing_root / f"{received_at[:10]}_{slot:04d}_{case_code}"
                case_dir.mkdir(parents=True, exist_ok=existing_operation is not None)
                destination = case_dir / f"mesh{temporary_path.suffix.casefold()}"
                if destination.exists():
                    if _sha256_file(destination) != source_sha:
                        raise HTTPException(409, {"code": "INGEST_RECOVERY_MESH_CONFLICT", "message": "La malla preparada no coincide con el reintento"})
                else:
                    shutil.copyfile(temporary_path, destination)
                delivered_sha = _sha256_file(destination)
                queue_visibility = "PENDING" if prepared else "ACTIVE"
                record = {
                    "schema_version": 2,
                    "date": received_at[:10],
                    "daily_slot": slot,
                    "daily_total": 0,
                    "case_code": case_code,
                    "source_mesh_sha256": source_sha,
                    "geometry_sha256": geometry_sha,
                    "delivered_stl_sha256": delivered_sha,
                    "triangle_count": int(features.get("faces", 0)),
                    "review_status": "AWAITING_HUMAN_REVIEW",
                    "queue_visibility": queue_visibility,
                    "origin_platform": platform_id,
                    "connector_id": connector_id,
                    "source_event_id_commitment": source_event_sha,
                    "original_filename_stored": False,
                    "received_at": received_at,
                }
                recovered_identity = load_private_identity(
                    path=private_identity_path, encryption_key=identity_encryption_key, case_code=case_code,
                )
                expected_recovery_identity = {
                    "patient_name": patient_name.strip(), "clinic_reference": clinic_reference.strip(),
                    "order_reference": order_reference.strip(), "source_event_id": source_event_id,
                }
                if recovered_identity is not None and not all(
                    secrets.compare_digest(str(recovered_identity.get(key, "")).encode("utf-8"), value.encode("utf-8"))
                    for key, value in expected_recovery_identity.items()
                ):
                    raise HTTPException(409, {"code": "SOURCE_IDENTITY_CONFLICT", "message": "El evento preparado está vinculado a otra identidad privada"})
                if recovered_identity is None:
                    store_private_identity(
                        path=private_identity_path, encryption_key=identity_encryption_key,
                        case_code=case_code, patient_name=patient_name,
                        clinic_reference=clinic_reference, order_reference=order_reference,
                        source_event_id=source_event_id, created_at=received_at,
                    )
                prepared.append(record)
                atomic_json_write(queue_state_path, state)
                if queue_history_path is not None:
                    if queue_history_path.exists():
                        history = json.loads(queue_history_path.read_text(encoding="utf-8"))
                    else:
                        history = {"schema_version": 2, "prepared": []}
                    history.setdefault("prepared", []).append(dict(record))
                    atomic_json_write(queue_history_path, history)
                intake_event = {
                    "schema_version": 1,
                    "event_type": "AUTHENTICATED_PLATFORM_INGEST",
                    "case_code": case_code,
                    "platform": platform_id,
                    "connector_id": connector_id,
                    "source_sha256": source_sha,
                    "geometry_sha256": geometry_sha,
                    "source_event_id_commitment": record["source_event_id_commitment"],
                    "original_filename_stored": False,
                    "received_at": received_at,
                }
                _append_jsonl_locked(runtime / "platform_intake.jsonl", intake_event, unique_key="source_sha256")
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

            case = resolve_prepared_case(record)
            if case is None:
                raise HTTPException(503, {"code": "QUEUE_CASE_MISSING", "message": "La malla preparada no está disponible"})
            return {
                "status": "STAGED_PENDING" if record.get("queue_visibility") == "PENDING" else "ENQUEUED",
                "case": public_queue_case(case),
            }
        finally:
            temporary_path.unlink(missing_ok=True)

    def promote_next_pending_case() -> None:
        if queue_state_path is None or not queue_state_path.exists():
            raise RuntimeError("QUEUE_STATE_UNAVAILABLE")
        with workflow_lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = json.loads(queue_state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError("QUEUE_STATE_UNAVAILABLE") from exc
            pending = next(
                (item for item in state.get("prepared", []) if item.get("queue_visibility") == "PENDING"),
                None,
            )
            if pending is None:
                raise RuntimeError("NO_PENDING_MESH")
            pending_case_code = str(pending.get("case_code", ""))
            promoted_at = _utc_now()
            if queue_history_path is not None:
                try:
                    history = json.loads(queue_history_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise RuntimeError("QUEUE_HISTORY_UNAVAILABLE") from exc
                history_pending = next(
                    (
                        item for item in history.get("prepared", [])
                        if str(item.get("case_code", "")) == pending_case_code
                    ),
                    None,
                )
                if history_pending is None:
                    raise RuntimeError("QUEUE_HISTORY_CASE_MISSING")
                history_pending["queue_visibility"] = "ACTIVE"
                history_pending["promoted_at"] = promoted_at
                atomic_json_write(queue_history_path, history)
            pending["queue_visibility"] = "ACTIVE"
            pending["promoted_at"] = promoted_at
            atomic_json_write(queue_state_path, state)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    @app.get("/api/platform-connectors/status")
    def platform_connectors_status():
        connectors = load_platform_connectors()
        return {"connectors": [{
            "connector_id": str(item.get("connector_id", "")),
            "display_name": str(item.get("display_name", item.get("connector_id", ""))),
            "enabled": bool(item.get("enabled", False)),
            "mode": str(item.get("mode", "")),
            "source_available": Path(str(item.get("source_root", ""))).is_dir(),
        } for item in connectors]}

    @app.post("/api/platform-connectors/scan")
    def scan_platform_connectors():
        return scan_read_only_connectors(
            load_platform_connectors(),
            log_path=runtime / "platform_intake.jsonl",
            now=_utc_now(),
        )

    @app.get("/api/review-queue")
    def review_queue():
        cases = resolve_queue_cases()
        return {"cases": [public_queue_case(case) for case in cases]}

    @app.post("/api/review-queue/next", status_code=201)
    def advance_review_queue():
        with (runtime / "queue_advance.lock").open("a+", encoding="utf-8") as advance_lock:
            fcntl.flock(advance_lock.fileno(), fcntl.LOCK_EX)
            cases = resolve_queue_cases()
            if not cases:
                raise HTTPException(409, {"code": "REVIEW_QUEUE_EMPTY", "message": "No hay una malla activa"})
            current = cases[-1]
            if not str(current["review_status"]).startswith("COMPLETED"):
                raise HTTPException(409, {
                    "code": "CURRENT_REVIEW_NOT_COMPLETED",
                    "message": "Guarda primero la revisión humana de la malla actual",
                })
            advance_callback = daily_advance_callback or promote_next_pending_case
            current_case_code = str(current["case_code"])
            try:
                advance_callback()
            except Exception as exc:
                raise HTTPException(503, {"code": "QUEUE_ADVANCE_FAILED", "message": "No se pudo preparar la siguiente malla"}) from exc
            updated_cases = resolve_queue_cases()
            if not updated_cases or str(updated_cases[-1]["case_code"]) == current_case_code:
                raise HTTPException(503, {"code": "QUEUE_ADVANCE_NO_CHANGE", "message": "La cola no avanzó"})
            public_case = public_queue_case(updated_cases[-1])
            fcntl.flock(advance_lock.fileno(), fcntl.LOCK_UN)
            return {"case": public_case}

    @app.get("/api/review-queue/{case_code}/mesh")
    def review_queue_mesh(case_code: str):
        case = queue_case(case_code)
        media_type = "model/stl" if case["mesh_format"] == "stl" else "application/octet-stream"
        return FileResponse(case["_mesh_path"], media_type=media_type, filename=f"{case_code}.{case['mesh_format']}")

    def register_assessment(assessment: dict[str, Any]) -> None:
        added = _append_jsonl_locked(
            assessments_path,
            assessment,
            unique_key="assessment_id",
        )
        if not added and assessment["assessment_id"] not in assessments:
            raise HTTPException(409, "La evaluación ya existe en almacenamiento persistente")
        assessments[assessment["assessment_id"]] = assessment

    def run_agent(
        *,
        path: Path,
        case_code: str,
        source_sha256: str,
        functional_class: str,
        question: str,
    ) -> dict[str, Any]:
        with (runtime / "analysis.lock").open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                features = mesh_features(path)
            except Exception as exc:
                raise HTTPException(422, {
                    "code": "MESH_NOT_EVALUABLE",
                    "message": "La malla no puede evaluarse con los límites técnicos configurados",
                }) from exc
            probability_incorrect = float(model.predict_proba([features])[0][1])
            rag_query = f"{question} {functional_class} scanbody congruencia escaneado implantes"
            citations = _rag_search(local_knowledge, rag_query)
            assessment = compose_assessment(
                case_code=case_code,
                source_sha256=source_sha256,
                features=features,
                probability_incorrect=probability_incorrect,
                citations=citations,
                model_version=str(benchmark.get("model_version", benchmark.get("run_id", "unknown"))),
                balanced_accuracy=float(benchmark["models"]["random_forest"]["balanced_accuracy"]),
                now=_utc_now(),
            )
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        assessment["functional_class"] = functional_class
        return assessment

    @app.post("/api/agent/analyze-demo")
    def analyze_demo(request: AnalyzeRequest):
        assessment = run_agent(
            path=mesh_path,
            case_code="AIQ-DEMO-SYNTHETIC",
            source_sha256=demo_source_sha256,
            functional_class=request.functional_class,
            question=request.question,
        )
        assessment["original_filename_stored"] = False
        register_assessment(assessment)
        return public_assessment(assessment)

    @app.post("/api/agent/analyze-queue/{case_code}")
    def analyze_queue(case_code: str, request: AnalyzeRequest):
        case = queue_case(case_code)
        if case.get("review_status") == "COMPLETED":
            raise HTTPException(409, {
                "code": "CASE_ALREADY_COMPLETED",
                "message": "El caso ya tiene una revisión humana persistida",
            })
        assessment = run_agent(
            path=case["_mesh_path"],
            case_code=case_code,
            source_sha256=case["source_mesh_sha256"],
            functional_class=request.functional_class,
            question=request.question,
        )
        assessment["original_filename_stored"] = False
        assessment["queue_source"] = "daily_read_only"
        assessment["daily_slot"] = case["daily_slot"]
        assessment["daily_total"] = case["daily_total"]
        assessment["duplicate_training_source"] = case["source_mesh_sha256"] in known_hashes
        register_assessment(assessment)
        return public_assessment(assessment)

    @app.post("/api/agent/analyze-upload")
    async def analyze_upload(
        file: Annotated[UploadFile, File()],
        functional_class: Annotated[str, Form(min_length=2, max_length=120)],
        question: Annotated[str, Form(max_length=500)] = "calidad técnica scanbody escaneado implantes",
    ):
        temporary_path, source_sha = await persist_platform_upload(file)
        suffix = temporary_path.suffix.casefold()
        intake = runtime / "intake"
        intake.mkdir(parents=True, exist_ok=True)
        stored = intake / f"mesh-{source_sha}{suffix}"
        if stored.exists():
            temporary_path.unlink(missing_ok=True)
        else:
            os.replace(temporary_path, stored)
        assessment = run_agent(
            path=stored,
            case_code=f"AIQ-{secrets.token_hex(8).upper()}",
            source_sha256=source_sha,
            functional_class=functional_class,
            question=question,
        )
        assessment["original_filename_stored"] = False
        assessment["duplicate_training_source"] = source_sha in known_hashes
        register_assessment(assessment)
        return public_assessment(assessment)

    @app.post("/api/reviews", status_code=201)
    def save_review(request: ReviewRequest, http_request: Request):
        reviewer_principal = str(
            getattr(http_request.state, "authenticated_username", None)
            or app_auth_username
            or "local-demo-reviewer"
        )
        reviews_path = runtime / "reviews.jsonl"
        review_lock_path = runtime / "review.lock"
        with review_lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            durable_assessments = _read_jsonl_bounded(assessments_path)
            assessment = next((
                item for item in reversed(durable_assessments)
                if item.get("assessment_id") == request.assessment_id
            ), None)
            if assessment is None:
                raise HTTPException(404, "Evaluación del agente no encontrada")
            queue_case_for_review: dict[str, Any] | None = None
            if assessment.get("queue_source") == "daily_read_only":
                queue_case_for_review = queue_case(str(assessment["case_code"]))
            if request.functional_class != assessment.get("functional_class"):
                raise HTTPException(409, "La función revisada no coincide con la función analizada")
            expected_judgment = (
                "CORRECT" if request.human_label == assessment["agent_output"]["verdict"] else "INCORRECT"
            )
            if request.judgment != expected_judgment:
                raise HTTPException(422, "El juicio humano contradice la etiqueta seleccionada")
            if expected_judgment == "INCORRECT" and not request.notes.strip():
                raise HTTPException(422, "La corrección humana requiere una observación técnica")

            prior_reviews = _read_jsonl_bounded(reviews_path)
            durable_training_hashes = {
                str(item["sha256"]) for item in manifest.get("records", [])
                if re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
            }
            durable_training_hashes.update(
                str(item["source_mesh_sha256"])
                for item in prior_reviews
                if re.fullmatch(r"[0-9a-f]{64}", str(item.get("source_mesh_sha256", "")))
            )
            existing_assessment_review = next((
                item for item in prior_reviews
                if item.get("assessment_id") == request.assessment_id
            ), None)
            if existing_assessment_review is not None:
                same_retry = (
                    secrets.compare_digest(str(existing_assessment_review.get("reviewer", "")), reviewer_principal)
                    and existing_assessment_review.get("human_label") == request.human_label
                    and bool(existing_assessment_review.get("agent_was_correct")) == (request.judgment == "CORRECT")
                    and existing_assessment_review.get("functional_class") == request.functional_class
                    and str(existing_assessment_review.get("change_reason", "")) == request.notes.strip()
                )
                if not same_retry:
                    raise HTTPException(409, "La evaluación ya tiene una revisión diferente")
                review = existing_assessment_review
                is_retry = True
            else:
                if queue_case_for_review is not None and queue_case_for_review.get("review_status") == "COMPLETED":
                    raise HTTPException(409, {
                        "code": "CASE_ALREADY_COMPLETED",
                        "message": "El caso ya tiene una revisión humana persistida",
                    })
                try:
                    review = record_feedback(
                        assessment=assessment,
                        reviewer=reviewer_principal,
                        human_label=request.human_label,
                        judgment=request.judgment,
                        notes=request.notes,
                        functional_class=request.functional_class,
                        known_training_hashes=durable_training_hashes,
                        log_path=reviews_path,
                        now=_utc_now(),
                    )
                except ValueError as exc:
                    raise HTTPException(409, str(exc)) from exc
                is_retry = False

            if assessment.get("queue_source") == "daily_read_only":
                if queue_case_for_review is None:
                    raise HTTPException(409, "El caso de cola no está disponible para completar la revisión")
                case = queue_case_for_review
                candidate_event = {
                    "schema_version": 1,
                    "event_type": "HUMAN_REVIEW_TRAINING_CANDIDATE",
                    "candidate_event_id": f"CAND-{review['review_id']}",
                    "review_id": review["review_id"],
                    "assessment_id": review["assessment_id"],
                    "case_code": review["case_code"],
                    "source_mesh_sha256": review["source_mesh_sha256"],
                    "geometry_sha256": geometry_sha256(case["_mesh_path"]),
                    "original_filename_public": False,
                    "human_label": review["human_label"],
                    "functional_class": review["functional_class"],
                    "previous_system_output": review["previous_system_output"],
                    "counts_as_new_training_mesh": bool(review["new_training_sample"]),
                    "group_id": None,
                    "group_assignment_status": "PENDING_PROVENANCE_GROUP",
                    "training_eligibility": "BLOCKED_UNTIL_GROUPED",
                    "automatic_retraining": False,
                    "promotion_status": "NO_PROMOTION",
                    "stable_model_changed": False,
                    "timestamp": review["timestamp"],
                }
                review["candidate_event_added"] = _append_jsonl_locked(
                    runtime / "training_candidates.jsonl", candidate_event, unique_key="review_id"
                )
                review["queue_status_updated"] = mark_queue_case_completed(
                    str(assessment["case_code"]), str(review["review_id"]), str(review["timestamp"])
                )
            if review.get("new_training_sample"):
                known_hashes.add(str(review["source_mesh_sha256"]))
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return public_review(review)

    @app.get("/api/reviews/latest")
    def latest_review(case_code: str):
        reviews_path = runtime / "reviews.jsonl"
        if not reviews_path.exists():
            raise HTTPException(404, "No hay rectificación humana para esta malla")
        reviews = _read_jsonl_bounded(reviews_path)
        reconciliations_path = runtime / "review_reconciliations.jsonl"
        invalid_review_ids: set[str] = set()
        if reconciliations_path.exists():
            reconciliations = _read_jsonl_bounded(reconciliations_path)
            invalid_review_ids = {item["invalid_review_id"] for item in reconciliations}
        effective = [item for item in reviews if
            item.get("case_code") == case_code
            and item.get("review_id") not in invalid_review_ids
        ]
        if not effective:
            raise HTTPException(404, "No hay rectificación humana efectiva para este caso")
        return public_review(effective[-1])

    @app.get("/api/training/status")
    def training_status():
        reviews_path = runtime / "reviews.jsonl"
        reviews = _read_jsonl_bounded(reviews_path)
        reconciliations_path = runtime / "review_reconciliations.jsonl"
        reconciliations = _read_jsonl_bounded(reconciliations_path)
        invalid_review_ids = {item["invalid_review_id"] for item in reconciliations}
        effective_reviews = [item for item in reviews if item.get("review_id") not in invalid_review_ids]
        new_unique = sum(bool(item.get("new_training_sample")) for item in effective_reviews)
        candidates_path = runtime / "training_candidates.jsonl"
        candidates = _read_jsonl_bounded(candidates_path)
        pending_group_assignment = sum(
            item.get("group_assignment_status") == "PENDING_PROVENANCE_GROUP" for item in candidates
        )
        ready_geometry_ids = {
            str(item["geometry_sha256"])
            for item in candidates
            if item.get("counts_as_new_training_mesh")
            and item.get("group_assignment_status") == "ASSIGNED"
            and item.get("group_id")
        }
        ready_grouped_candidates = len(ready_geometry_ids)
        gate_ready = ready_grouped_candidates >= 6
        if pending_group_assignment:
            gate_reason = (
                f"{pending_group_assignment} muestras pendientes de grupo clínico; "
                "no pueden entrar en evaluación hasta evitar fuga de caso"
            )
        elif not gate_ready:
            gate_reason = "Se requieren al menos 6 geometrías nuevas con grupos clínicos separados"
        else:
            gate_reason = "Listo para evaluación agrupada; promoción manual todavía obligatoria"
        return {
            "run_id": benchmark.get("run_id", "unknown"),
            "meshes": benchmark["dataset"]["meshes"],
            "case_groups": benchmark["dataset"]["case_groups"],
            "balanced_accuracy": benchmark["models"]["random_forest"]["balanced_accuracy"],
            "incorrect_recall": benchmark["models"]["random_forest"]["incorrect_recall"],
            "audit_review_events": len(reviews),
            "human_reviews_received": len(effective_reviews),
            "reconciled_duplicates": len(invalid_review_ids),
            "new_unique_training_samples": new_unique,
            "revalidations": len(effective_reviews) - new_unique,
            "candidate_records": len(candidates),
            "pending_group_assignment": pending_group_assignment,
            "ready_grouped_candidates": ready_grouped_candidates,
            "next_candidate_gate": {
                "ready": gate_ready,
                "minimum_new_unique_samples": 6,
                "reason": gate_reason,
            },
            "promotion": "NO_PROMOTION",
            "stable_model_changed": False,
        }

    if static_root is not None:
        index_file = static_root / "index.html"
        if not index_file.is_file():
            raise ValueError("El directorio estático no contiene index.html")
        assets_dir = static_root / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_frontend(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(404, "Ruta no encontrada")
            requested = (static_root / full_path).resolve()
            if requested.is_relative_to(static_root) and requested.is_file():
                return FileResponse(requested)
            return FileResponse(index_file)

    return app


def _queue_advance_callback(script_path: Path) -> Callable[[], None]:
    def advance() -> None:
        env = os.environ.copy()
        env["ABUTMENTIQ_DAILY_TARGET"] = "0"
        result = subprocess.run(
            ["/bin/bash", str(script_path)],
            env=env,
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "QUEUE_ADVANCE_FAILED").strip()[-1000:]
            raise RuntimeError(detail)

    return advance


def default_app() -> FastAPI:
    project = Path(__file__).resolve().parents[1]
    asset_root = Path(os.environ.get("ABUTMENTIQ_ASSET_ROOT", project / "deploy_assets"))
    data_root = Path(os.environ.get("ABUTMENTIQ_DATA_ROOT", project))
    runtime_dir = Path(os.environ.get("ABUTMENTIQ_RUNTIME_DIR", data_root / "runtime"))
    queue_state = Path(os.environ.get("ABUTMENTIQ_QUEUE_STATE_PATH", data_root / "queue_state.json"))
    queue_root = Path(os.environ.get("ABUTMENTIQ_QUEUE_ROOT", data_root / "queue"))
    queue_history = Path(os.environ.get("ABUTMENTIQ_QUEUE_HISTORY_PATH", data_root / "queue_history.json"))
    connector_config = Path(os.environ.get("ABUTMENTIQ_PLATFORM_CONNECTORS_PATH", asset_root / "platform_connectors.json"))
    advance_script_raw = os.environ.get("ABUTMENTIQ_QUEUE_ADVANCE_SCRIPT")
    advance_callback = None
    if advance_script_raw:
        advance_script = Path(advance_script_raw)
        if not advance_script.is_file():
            raise RuntimeError("ABUTMENTIQ_QUEUE_ADVANCE_SCRIPT no existe")
        advance_callback = _queue_advance_callback(advance_script)

    app_username = os.environ.get("ABUTMENTIQ_APP_USERNAME")
    app_password = os.environ.get("ABUTMENTIQ_APP_PASSWORD")
    local_demo = os.environ.get("ABUTMENTIQ_LOCAL_DEMO", "false").casefold() in {"1", "true", "yes"}
    if local_demo and (app_username or app_password):
        raise RuntimeError("El modo demo local no puede combinarse con credenciales de producción")
    if not local_demo and (not app_username or not app_password):
        raise RuntimeError("La autenticación de la aplicación es obligatoria fuera del modo demo local explícito")
    allowed_origin_raw = os.environ.get("ABUTMENTIQ_ALLOWED_ORIGIN", "").strip()
    if not local_demo and not allowed_origin_raw:
        raise RuntimeError("ABUTMENTIQ_ALLOWED_ORIGIN es obligatorio en producción")
    allowed_origins = tuple(item.strip() for item in allowed_origin_raw.split(",") if item.strip())
    dist_dir = project / "dist"

    return create_app(
        runtime_dir=runtime_dir,
        demo_mesh=Path(os.environ.get("ABUTMENTIQ_DEMO_MESH", asset_root / "synthetic_dental_arch.stl")),
        model_path=Path(os.environ.get("ABUTMENTIQ_MODEL_PATH", asset_root / "bootstrap_model.joblib")),
        benchmark_path=Path(os.environ.get("ABUTMENTIQ_BENCHMARK_PATH", asset_root / "model_benchmark.json")),
        manifest_path=Path(os.environ.get("ABUTMENTIQ_MANIFEST_PATH", asset_root / "seed_manifest.json")),
        knowledge_db=Path(os.environ.get("ABUTMENTIQ_KNOWLEDGE_DB", asset_root / "knowledge.db")),
        daily_state_path=queue_state,
        daily_outgoing_root=queue_root,
        daily_history_path=queue_history,
        daily_advance_callback=advance_callback,
        platform_connectors_path=connector_config,
        platform_ingest_token=os.environ.get("ABUTMENTIQ_PLATFORM_INGEST_TOKEN"),
        platform_ingest_max_bytes=int(os.environ.get("ABUTMENTIQ_PLATFORM_MAX_BYTES", str(100 * 1024 * 1024))),
        identity_encryption_key=os.environ.get("ABUTMENTIQ_IDENTITY_ENCRYPTION_KEY"),
        static_dir=dist_dir if dist_dir.is_dir() else None,
        app_auth_username=app_username,
        app_auth_password=app_password,
        allowed_origins=allowed_origins,
    )
