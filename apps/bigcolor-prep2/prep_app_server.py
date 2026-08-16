from __future__ import annotations

import json
import mimetypes
import shutil
import tempfile
import uuid
import csv
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from prep_engine import (
    DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
    DEFAULT_RAY_MAX_DEPTH_MM,
    DEFAULT_RAY_SAMPLE_COUNT,
    MATERIAL_PROFILES,
    NORMAL_RAY_DIRECTIONS,
    UNIT_SCALE_TO_MM,
    analyze_case,
)


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8787
LOCAL_RANKING_SUMMARY = ROOT_DIR / "outputs" / "pedro-local-ranking-2026-08-06-summary.csv"
LOCAL_RANKING_NUMERIC_COLUMNS = {
    "neighborhood_radius_mm",
    "before_ray_hit_ratio",
    "after_ray_hit_ratio",
    "hit_ratio_delta",
    "local_icp_p95_mm",
    "local_icp_rotation_deg",
    "local_icp_translation_mm",
}


class MultipartError(ValueError):
    pass


def _parse_options(header_value: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in header_value.split(";")]
    options: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        options[key.strip().lower()] = value
    return parts[0].lower(), options


def _parse_multipart(body: bytes, content_type: str) -> dict[str, dict[str, Any]]:
    media_type, options = _parse_options(content_type)
    boundary = options.get("boundary")
    if media_type != "multipart/form-data" or not boundary:
        raise MultipartError("Expected multipart/form-data with boundary.")

    delimiter = b"--" + boundary.encode("utf-8")
    fields: dict[str, dict[str, Any]] = {}
    for raw_part in body.split(delimiter):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        if part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")
        header_blob, separator, payload = part.partition(b"\r\n\r\n")
        if not separator:
            continue
        headers: dict[str, str] = {}
        for line in header_blob.decode("utf-8", errors="replace").split("\r\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
        disposition = headers.get("content-disposition", "")
        _, disposition_options = _parse_options(disposition)
        name = disposition_options.get("name")
        if not name:
            continue
        fields[name] = {
            "filename": disposition_options.get("filename"),
            "content_type": headers.get("content-type"),
            "data": payload.rstrip(b"\r\n"),
        }
    return fields


def _field_text(fields: dict[str, dict[str, Any]], name: str, default: str) -> str:
    value = fields.get(name)
    if not value:
        return default
    return value["data"].decode("utf-8", errors="replace").strip() or default


def _write_uploaded_stl(fields: dict[str, dict[str, Any]], name: str, target_dir: Path) -> Path:
    field = fields.get(name)
    if not field or not field["data"]:
        raise MultipartError(f"Missing uploaded STL field: {name}")
    filename = str(field.get("filename") or f"{name}.stl")
    if not filename.lower().endswith(".stl"):
        raise MultipartError(f"{name} must be an STL file.")
    target = target_dir / f"{name}_{uuid.uuid4().hex}.stl"
    target.write_bytes(field["data"])
    return target


def _write_uploaded_json(fields: dict[str, dict[str, Any]], name: str, target_dir: Path) -> Path | None:
    field = fields.get(name)
    if not field or not field["data"]:
        return None
    filename = str(field.get("filename") or f"{name}.json")
    if not filename.lower().endswith(".json"):
        raise MultipartError(f"{name} must be a JSON file.")
    target = target_dir / f"{name}_{uuid.uuid4().hex}.json"
    target.write_bytes(field["data"])
    return target


def _records_from_table(table) -> list[dict[str, Any]]:
    return json.loads(table.to_json(orient="records", force_ascii=False))


def _analysis_for_response(analysis: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in analysis.items() if not key.startswith("_")}


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_local_ranking_summary(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows: list[dict[str, Any]] = []
        for row in csv.DictReader(handle):
            parsed: dict[str, Any] = dict(row)
            for column in LOCAL_RANKING_NUMERIC_COLUMNS:
                parsed[column] = _parse_float(row.get(column))
            rows.append(parsed)
    return rows


def _local_ranking_sort_key(row: dict[str, Any]) -> tuple[float, float, float, float, int, str]:
    p95 = row.get("local_icp_p95_mm")
    rotation = row.get("local_icp_rotation_deg")
    translation = row.get("local_icp_translation_mm")
    after = row.get("after_ray_hit_ratio")
    try:
        sample_count = int(str(row.get("preop_sample_count") or "0"))
    except ValueError:
        sample_count = 0
    return (
        float(p95) if isinstance(p95, float) else 999999.0,
        -(float(after) if isinstance(after, float) else -1.0),
        float(rotation) if isinstance(rotation, float) else 999999.0,
        float(translation) if isinstance(translation, float) else 999999.0,
        -sample_count,
        str(row.get("run") or ""),
    )


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        raw = str(row.get("candidate_reason") or "")
        for reason in [part.strip() for part in raw.split(",") if part.strip()]:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _local_ranking_payload(path: Path = LOCAL_RANKING_SUMMARY, top: int = 15) -> dict[str, Any]:
    if not path.exists():
        return {
            "available": False,
            "source": str(path.relative_to(ROOT_DIR)),
            "rowsEvaluated": 0,
            "decision": "Panel pendiente: no existe el CSV consolidado de ranking local.",
        }
    rows = _load_local_ranking_summary(path)
    sorted_rows = sorted(rows, key=_local_ranking_sort_key)
    return {
        "available": True,
        "source": str(path.relative_to(ROOT_DIR)),
        "rowsEvaluated": len(rows),
        "candidateStatusCounts": _counts(rows, "candidate_status"),
        "safeToApplyCounts": _counts(rows, "safe_to_apply_local_transform"),
        "mainRejectionReasons": _reason_counts(rows),
        "bestPatch": sorted_rows[0] if sorted_rows else None,
        "topPatches": sorted_rows[: max(1, top)],
        "decision": (
            "ICP local queda como QA/ranking no aplicado. No alimentar transforms locales "
            "al motor principal hasta validar repetibilidad, registro y umbrales explicitos."
        ),
        "clinicalCaveat": "Este panel no valida precision clinica ni autoriza uso clinico.",
    }


class PrepAppHandler(SimpleHTTPRequestHandler):
    server_version = "BigColorPREP/0.2"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path in {"/", ""}:
            self.path = "/BigColor_PREP_2_APP.html"
        if self.path == "/api/health":
            self._send_json(
                {
                    "ok": True,
                    "engine": "prep_engine.py",
                    "materials": sorted(MATERIAL_PROFILES),
                    "inputUnits": sorted(UNIT_SCALE_TO_MM),
                    "defaultExactSurfaceVertexLimit": DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
                    "measurementMethods": ["fast_vertex", "exact_surface", "normal_ray"],
                    "normalRayDirections": list(NORMAL_RAY_DIRECTIONS),
                    "defaultRaySampleCount": DEFAULT_RAY_SAMPLE_COUNT,
                    "defaultRayMaxDepthMm": DEFAULT_RAY_MAX_DEPTH_MM,
                }
            )
            return
        if self.path == "/api/local-ranking":
            self._send_json(_local_ranking_payload())
            return
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint.")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                raise MultipartError("Empty request body.")
            fields = _parse_multipart(self.rfile.read(content_length), self.headers.get("Content-Type", ""))
            material = _field_text(fields, "material", "demo_veneer")
            arch = _field_text(fields, "arch", "S")
            input_unit = _field_text(fields, "input_unit", "mm")
            if input_unit not in UNIT_SCALE_TO_MM:
                raise MultipartError(f"Unknown input_unit: {input_unit}. Available: {', '.join(sorted(UNIT_SCALE_TO_MM))}")
            mode = _field_text(fields, "mode", "upload")
            exact_surface = _field_text(fields, "exact_surface", "0") == "1"
            measurement_method = _field_text(fields, "measurement_method", "fast_vertex")
            if exact_surface:
                measurement_method = "exact_surface"
            if measurement_method not in {"fast_vertex", "exact_surface", "normal_ray"}:
                raise MultipartError("measurement_method must be fast_vertex, exact_surface or normal_ray")
            ray_sample_count = int(_field_text(fields, "ray_sample_count", str(DEFAULT_RAY_SAMPLE_COUNT)))
            if ray_sample_count < 0:
                raise MultipartError("ray_sample_count must be >= 0")
            ray_max_depth_mm = float(_field_text(fields, "ray_max_depth_mm", str(DEFAULT_RAY_MAX_DEPTH_MM)))
            if ray_max_depth_mm <= 0:
                raise MultipartError("ray_max_depth_mm must be > 0")
            ray_direction = _field_text(fields, "ray_direction", "bidirectional")
            if ray_direction not in NORMAL_RAY_DIRECTIONS:
                raise MultipartError(f"ray_direction must be one of: {', '.join(NORMAL_RAY_DIRECTIONS)}")
            apply_icp = _field_text(fields, "apply_icp", "0") == "1"
            icp_report_only = _field_text(fields, "icp_report_only", "0") == "1"

            with tempfile.TemporaryDirectory(prefix="bigcolor_prep_upload_") as tmp:
                tmp_dir = Path(tmp)
                if mode == "demo":
                    preop_path = ROOT_DIR / "assets" / "preoperatorio_sup.stl"
                    waxup_path = ROOT_DIR / "assets" / "encerado_sup.stl"
                else:
                    preop_path = _write_uploaded_stl(fields, "preop", tmp_dir)
                    waxup_path = _write_uploaded_stl(fields, "waxup", tmp_dir)
                landmarks_path = _write_uploaded_json(fields, "landmarks", tmp_dir)

                analysis, table = analyze_case(
                    preop_path=preop_path,
                    waxup_path=waxup_path,
                    material=material,
                    arch=arch,
                    apply_icp=apply_icp,
                    icp_report_only=icp_report_only,
                    landmarks_path=landmarks_path,
                    input_unit=input_unit,
                    exact_surface=exact_surface,
                    exact_surface_vertex_limit=DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
                    measurement_method=measurement_method,
                    ray_sample_count=ray_sample_count,
                    ray_max_depth_mm=ray_max_depth_mm,
                    ray_direction=ray_direction,
                )

            self._send_json(
                {
                    "ok": True,
                    "analysis": _analysis_for_response(analysis),
                    "table": _records_from_table(table),
                    "rowCount": int(len(table)),
                }
            )
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                },
                status=HTTPStatus.BAD_REQUEST,
            )

    def guess_type(self, path: str) -> str:
        if path.endswith(".stl"):
            return "model/stl"
        return mimetypes.guess_type(path)[0] or super().guess_type(path)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Serve BigColor PREP 2 app with Python analysis API.")
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Use 0.0.0.0 for LAN access.")
    args = parser.parse_args()

    print("BigColor PREP 2 metrics app")
    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    print(f"URL: http://{display_host}:{args.port}/BigColor_PREP_2_APP.html")
    print(f"Project: {ROOT_DIR}")
    print("Engine: prep_engine.py via /api/analyze")
    print("Clinical caveat: technical QA until registration, units and repeatability are validated.")

    handler = PrepAppHandler
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
