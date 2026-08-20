from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from .mesh_features import DEFAULT_MAX_FACES, DEFAULT_MAX_VERTICES, validate_mesh_resource_limits

SUPPORTED_MESH_EXTENSIONS = {".stl", ".ply"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def geometry_sha256(path: Path) -> str:
    validate_mesh_resource_limits(path)
    loaded = trimesh.load(path, process=False, force="scene")
    if isinstance(loaded, trimesh.Scene):
        if not loaded.geometry:
            raise ValueError("La malla no contiene geometría")
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded
    if len(mesh.faces) > DEFAULT_MAX_FACES:
        raise ValueError("La malla contiene demasiadas caras tras parseo")
    if len(mesh.vertices) > DEFAULT_MAX_VERTICES:
        raise ValueError("La malla contiene demasiados vértices tras parseo")
    triangles = np.asarray(mesh.triangles, dtype=np.float64)
    if triangles.size == 0:
        raise ValueError("La malla no contiene triángulos")
    quantized = np.rint(triangles * 1_000_000.0).astype("<i8", copy=False)
    vertex_order = np.lexsort(
        (quantized[:, :, 2], quantized[:, :, 1], quantized[:, :, 0]), axis=1
    )
    canonical_triangles = np.take_along_axis(quantized, vertex_order[:, :, None], axis=1)
    rows = canonical_triangles.reshape((-1, 9))
    row_order = np.lexsort(tuple(rows[:, index] for index in reversed(range(rows.shape[1]))))
    canonical = np.ascontiguousarray(rows[row_order], dtype="<i8")
    return hashlib.sha256(canonical.tobytes()).hexdigest()


def scan_read_only_connectors(
    connectors: list[dict[str, Any]],
    *,
    log_path: Path | str,
    now: str | None = None,
    max_mesh_bytes: int = 100 * 1024 * 1024,
    max_candidates: int = 1000,
) -> dict[str, Any]:
    received_at = now or datetime.now(timezone.utc).isoformat()
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "connectors_scanned": 0,
        "new_source_events": 0,
        "new_unique_geometries": 0,
        "geometry_duplicates": 0,
        "errors": [],
    }
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        known_sources: set[str] = set()
        known_geometries: set[str] = set()
        case_codes_by_geometry: dict[str, str] = {}
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            source_hash = event.get("source_sha256")
            geometry_hash = event.get("geometry_sha256")
            if source_hash:
                known_sources.add(str(source_hash))
            if geometry_hash:
                known_geometries.add(str(geometry_hash))
                if event.get("public_case_code"):
                    case_codes_by_geometry[str(geometry_hash)] = str(event["public_case_code"])
        handle.seek(0, os.SEEK_END)
        for connector in connectors:
            if not connector.get("enabled", False):
                continue
            connector_id = str(connector.get("connector_id", ""))
            if re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", connector_id) is None:
                result["errors"].append({"connector_id": connector_id, "code": "INVALID_CONNECTOR_ID"})
                continue
            if connector.get("mode") != "read_only":
                result["errors"].append({"connector_id": connector_id, "code": "READ_ONLY_REQUIRED"})
                continue
            source_root = Path(str(connector.get("source_root", "")))
            if not source_root.is_dir():
                result["errors"].append({"connector_id": connector_id, "code": "SOURCE_UNAVAILABLE"})
                continue
            result["connectors_scanned"] += 1
            candidates: list[Path] = []
            candidate_limit_reached = False
            for candidate in source_root.rglob("*"):
                if (
                    candidate.is_file()
                    and not candidate.is_symlink()
                    and candidate.suffix.casefold() in SUPPORTED_MESH_EXTENSIONS
                    and not candidate.name.startswith("._")
                ):
                    if len(candidates) >= max_candidates:
                        candidate_limit_reached = True
                        break
                    candidates.append(candidate)
            if candidate_limit_reached:
                result["errors"].append({
                    "connector_id": connector_id,
                    "code": "SCAN_CANDIDATE_LIMIT_REACHED",
                })
            for mesh_path in sorted(candidates):
                try:
                    size_bytes = mesh_path.stat().st_size
                    if size_bytes > max_mesh_bytes:
                        result["errors"].append({
                            "connector_id": connector_id,
                            "code": "MESH_TOO_LARGE",
                        })
                        continue
                    source_sha = _sha256_file(mesh_path)
                    if source_sha in known_sources:
                        continue
                    geometry_sha = geometry_sha256(mesh_path)
                    is_new_geometry = geometry_sha not in known_geometries
                    public_case_code = case_codes_by_geometry.get(geometry_sha)
                    if public_case_code is None:
                        public_case_code = f"AIQ-{secrets.token_hex(6).upper()}"
                        case_codes_by_geometry[geometry_sha] = public_case_code
                    event = {
                        "schema_version": 1,
                        "event_type": "READ_ONLY_PLATFORM_INTAKE",
                        "connector_id": connector_id,
                        "connector_name": str(connector.get("display_name", connector_id)),
                        "source_mode": "read_only",
                        "source_sha256": source_sha,
                        "geometry_sha256": geometry_sha,
                        "public_case_code": public_case_code,
                        "mesh_format": mesh_path.suffix.casefold().lstrip("."),
                        "size_bytes": size_bytes,
                        "review_status": "PENDING_AGENT_REVIEW" if is_new_geometry else "GEOMETRY_DUPLICATE",
                        "counts_as_new_training_mesh": is_new_geometry,
                        "duplicate_reason": None if is_new_geometry else "KNOWN_GEOMETRY",
                        "original_filename_public": False,
                        "received_at": received_at,
                    }
                    handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    known_sources.add(source_sha)
                    known_geometries.add(geometry_sha)
                    result["new_source_events"] += 1
                    if is_new_geometry:
                        result["new_unique_geometries"] += 1
                    else:
                        result["geometry_duplicates"] += 1
                except Exception as exc:
                    result["errors"].append({
                        "connector_id": connector_id,
                        "code": "MESH_READ_ERROR",
                        "detail": type(exc).__name__,
                    })
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return result
