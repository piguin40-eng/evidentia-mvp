#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$BASH_SOURCE")/.." && pwd)"
if [[ "$#" -lt 1 ]]; then
  echo "Usage: scripts/clean_restore_smoke_test.sh <backup.tar.gz>" >&2
  exit 2
fi

ARCHIVE="$1"
PORT="$(printenv EVIDENTIA_RESTORE_TEST_PORT || true)"
if [[ -z "$PORT" ]]; then
  PORT="8894"
fi
BASE_URL="http://127.0.0.1:$PORT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="$ROOT/qa/clean-restore"
REPORT="$OUT_DIR/clean-restore-$STAMP.md"
QUESTION="$(printenv QUESTION || true)"
if [[ -z "$QUESTION" ]]; then
  QUESTION="Que conocimiento conecta estetica, laboratorio y aprendizaje?"
fi

if [[ ! -f "$ARCHIVE" ]]; then
  echo "Backup archive not found: $ARCHIVE" >&2
  exit 2
fi

for required in curl python3; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "Missing required command: $required" >&2
    exit 2
  fi
done

mkdir -p "$OUT_DIR"
staging="$(mktemp -d)"
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
    wait "$server_pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$staging"
}
trap cleanup EXIT

"$ROOT/scripts/evidentia_backup_restore.sh" verify-restore "$ARCHIVE" >"$OUT_DIR/verify-restore-$STAMP.txt"
tar -xzf "$ARCHIVE" -C "$staging"

(
  cd "$ROOT"
  EVIDENTIA_DATA_DIR="$staging/data" \
  EVIDENTIA_PORT="$PORT" \
  EVIDENTIA_HOST="127.0.0.1" \
  EVIDENTIA_BASIC_AUTH_USER="" \
  EVIDENTIA_BASIC_AUTH_PASSWORD="" \
  python3 server.py
) >"$OUT_DIR/server-$STAMP.log" 2>&1 &
server_pid="$!"

ready=false
for _ in $(seq 1 30); do
  if curl -fsS --max-time 2 "$BASE_URL/api/healthz" >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 1
done

if [[ "$ready" != true ]]; then
  echo "Clean restore server did not become ready on $BASE_URL" >&2
  tail -80 "$OUT_DIR/server-$STAMP.log" >&2 || true
  exit 2
fi

health_json="$OUT_DIR/health-$STAMP.json"
rag_json="$OUT_DIR/rag-$STAMP.json"
ai_json="$OUT_DIR/ai-$STAMP.json"
chat_json="$OUT_DIR/chat-$STAMP.json"
export_json="$OUT_DIR/knowledge-bundle-$STAMP.json"

curl -fsS --max-time 7 -H 'Accept: application/json' "$BASE_URL/api/health" >"$health_json"
curl -fsS --max-time 7 -H 'Accept: application/json' "$BASE_URL/api/rag/stats" >"$rag_json"
curl -fsS --max-time 7 -H 'Accept: application/json' "$BASE_URL/api/ai/status" >"$ai_json"
python3 - "$QUESTION" <<'PY' | curl -fsS --max-time 20 -X POST "$BASE_URL/api/chat" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  --data-binary @- >"$chat_json"
import json
import sys
print(json.dumps({"question": sys.argv[1]}, ensure_ascii=False))
PY
curl -fsS --max-time 12 -H 'Accept: application/json' "$BASE_URL/api/connectors/export" >"$export_json"

python3 - "$REPORT" "$ARCHIVE" "$BASE_URL" "$QUESTION" "$health_json" "$rag_json" "$ai_json" "$chat_json" "$export_json" "$OUT_DIR/verify-restore-$STAMP.txt" <<'PY'
import json
from pathlib import Path
import sys

report, archive, base_url, question, health_path, rag_path, ai_path, chat_path, export_path, verify_path = sys.argv[1:]

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

health = load(health_path)
rag = load(rag_path)
ai = load(ai_path)
chat = load(chat_path)
bundle = load(export_path)

sources = chat.get("sources") or []
records = int(health.get("records") or 0)
chunks = int(rag.get("chunks") or 0)
sqlite_chunks = int(rag.get("sqliteChunks") or 0)
compact_chunks = int(rag.get("compactVectorChunks") or 0)
bundle_records = len(bundle.get("records") or [])
bundle_chunks = len(bundle.get("chunks") or [])
pass_gate = records >= 3 and (chunks >= 3 or sqlite_chunks >= 3) and len(sources) >= 1 and bundle_records >= 3
result = "PASS" if pass_gate else "BLOCKED"
mode = "compact vector local" if chunks >= 3 else "fallback SQLite local con fuentes"
verify_text = Path(verify_path).read_text(encoding="utf-8").strip()
stamp = Path(report).stem.replace("clean-restore-", "")
verify_block = "\n".join("    " + line for line in verify_text.splitlines())

lines = [
    "# Evidentia Clean Restore Smoke Test",
    "",
    f"Fecha UTC: {stamp}",
    f"Backup probado: {archive}",
    f"Base URL temporal: {base_url}",
    f"Resultado: {result}",
    "",
    "## Estado Restaurado",
    "",
    f"- Registros locales: {records}",
    f"- Chunks compact vector: {compact_chunks}",
    f"- Chunks SQLite: {sqlite_chunks}",
    f"- Chunks recuperables reportados: {chunks}",
    f"- Modo de recuperacion: {mode}",
    f"- Fuentes devueltas por chat: {len(sources)}",
    f"- Registros en knowledge bundle: {bundle_records}",
    f"- Chunks en knowledge bundle: {bundle_chunks}",
    f"- IA externa activada: {ai.get('enabled', 'unknown')}",
    f"- Proveedor IA: {ai.get('provider', 'none')}",
    "",
    "## Pregunta Probada",
    "",
    question,
    "",
    "## Verificacion De Backup",
    "",
    verify_block,
    "",
    "## Puerta Comercial",
    "",
]
if pass_gate:
    lines.extend([
        "- La copia restaurada arranca en un servidor temporal sin tocar data/ activo.",
        "- La copia responde salud, RAG, chat con fuentes y export de knowledge bundle.",
        "- Se puede explicar como prueba interna de recuperacion local antes de piloto.",
    ])
else:
    lines.extend([
        "- No usar este backup como evidencia de piloto hasta resolver los bloqueos.",
        "- Revisar los JSON generados en este directorio para localizar el fallo.",
    ])

Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
if not pass_gate:
    raise SystemExit(2)
PY

echo "$REPORT"
