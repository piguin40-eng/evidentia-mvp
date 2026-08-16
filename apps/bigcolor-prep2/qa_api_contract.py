from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from prep_app_server import PrepAppHandler


ROOT = Path(__file__).resolve().parent


class QuietPrepAppHandler(PrepAppHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def _fail(message: str) -> None:
    raise SystemExit(f"QA_API_CONTRACT_FAIL: {message}")


def _multipart_body(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----BigColorPrepQaBoundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _walk_keys(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).startswith("_"):
                paths.append(child_path)
            paths.extend(_walk_keys(child, child_path))
        return paths
    if isinstance(value, list):
        paths = []
        for index, child in enumerate(value):
            paths.extend(_walk_keys(child, f"{prefix}[{index}]"))
        return paths
    return []


def _post_demo_analyze(port: int) -> tuple[int, dict[str, Any]]:
    body, content_type = _multipart_body(
        {
            "mode": "demo",
            "material": "ips_emax_press",
            "measurement_method": "normal_ray",
            "ray_direction": "bidirectional",
        }
    )
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=120)
    try:
        connection.request(
            "POST",
            "/api/analyze",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        return response.status, payload
    finally:
        connection.close()


def check_demo_analyze_endpoint() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietPrepAppHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        status, payload = _post_demo_analyze(port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    if status != 200:
        _fail(f"/api/analyze devolvio HTTP {status}: {payload.get('error')}")
    if payload.get("ok") is not True:
        _fail(f"/api/analyze ok=False: {payload.get('error')}")
    if int(payload.get("rowCount") or 0) <= 0:
        _fail("/api/analyze no devolvio filas")

    analysis = payload.get("analysis") or {}
    distance = analysis.get("distance") or {}
    if distance.get("method") != "normal_ray_surface_hybrid":
        _fail(f"distance.method inesperado: {distance.get('method')!r}")
    qa_gate = analysis.get("qa_gate") or {}
    if qa_gate.get("status") != "blocked_for_clinical_use":
        _fail(f"qa_gate.status inesperado: {qa_gate.get('status')!r}")

    internal_keys = _walk_keys(payload)
    if internal_keys:
        _fail(f"El JSON del API expone campos internos: {internal_keys[:5]}")

    rows = payload.get("table") or []
    if not rows:
        _fail("/api/analyze no devolvio tabla")
    first_row = rows[0]
    if first_row.get("Deficit display ES") != "no calculable como delta clinico":
        _fail(f"Deficit display ES inesperado: {first_row.get('Deficit display ES')!r}")
    if first_row.get("Material-zone join status") != "exact_material_profile_zone":
        _fail(f"Material-zone join status inesperado: {first_row.get('Material-zone join status')!r}")
    viewer_sentence = str(first_row.get("Viewer sentence ES") or "")
    required_sentence_tokens = [
        "Diente ",
        ", zona ",
        ": medido ",
        "; requerido ",
        "; material ",
        "; color ",
        "; accion tecnica ",
        "; caveat ",
    ]
    if not all(token in viewer_sentence for token in required_sentence_tokens):
        _fail(f"Viewer sentence ES no cumple contrato 2026-08-16: {viewer_sentence!r}")
    if "deficit" in viewer_sentence.lower():
        _fail(f"Viewer sentence ES bloqueada no debe vender deficit clinico: {viewer_sentence!r}")


def main() -> None:
    check_demo_analyze_endpoint()
    print("QA_API_CONTRACT_OK")
    print("endpoint=/api/analyze")
    print("mode=demo")
    print("material=ips_emax_press")
    print("measurement_method=normal_ray")


if __name__ == "__main__":
    main()
