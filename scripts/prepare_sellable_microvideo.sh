#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8892}"
OUT_DIR="${OUT_DIR:-${ROOT}/qa/microvideo}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
MANIFEST="${OUT_DIR}/microvideo-ready-${STAMP}.md"
QUESTION="${QUESTION:-Que conocimiento conecta estetica, laboratorio y aprendizaje?}"

mkdir -p "${OUT_DIR}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 2
  fi
}

fetch_json() {
  local path="$1"
  curl -fsS --max-time 5 -H 'Accept: application/json' "${BASE_URL}${path}"
}

post_chat() {
  python3 - "$QUESTION" <<'PY' | curl -fsS --max-time 10 -X POST "$BASE_URL/api/chat" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json' \
    --data-binary @-
import json
import sys
print(json.dumps({"question": sys.argv[1]}, ensure_ascii=False))
PY
}

json_value() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path, key = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
value = payload
for part in key.split("."):
    value = value.get(part, None) if isinstance(value, dict) else None
print("" if value is None else value)
PY
}

need curl
need python3

health_json="${OUT_DIR}/health-${STAMP}.json"
rag_json="${OUT_DIR}/rag-${STAMP}.json"
ai_json="${OUT_DIR}/ai-${STAMP}.json"
chat_json="${OUT_DIR}/chat-${STAMP}.json"
export_json="${OUT_DIR}/knowledge-bundle-${STAMP}.json"

fetch_json /api/health >"${health_json}"
fetch_json /api/rag/stats >"${rag_json}"
fetch_json /api/ai/status >"${ai_json}"
post_chat >"${chat_json}"
fetch_json /api/connectors/export >"${export_json}"

records="$(json_value "${health_json}" records)"
chunks="$(json_value "${rag_json}" chunks)"
sqlite_chunks="$(json_value "${rag_json}" sqliteChunks)"
sources="$(python3 - "${chat_json}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(len(payload.get("sources") or []))
PY
)"

if [[ "${chunks:-0}" -ge 3 ]]; then
  retrieval_mode="Chroma vectorial"
  retrieval_warning="Sin advertencia automatica de recuperacion."
elif [[ "${sqlite_chunks:-0}" -ge 3 ]]; then
  retrieval_mode="fallback SQLite local con fuentes"
  retrieval_warning="Chroma esta vacio: en el video decir modo local con fuentes, no RAG vectorial completo."
else
  retrieval_mode="no vendible"
  retrieval_warning="No hay chunks suficientes para preparar demo."
fi

if [[ "${records:-0}" -lt 3 ]]; then
  echo "Demo gate failed: expected at least 3 records, got ${records:-0}" >&2
  exit 2
fi

if [[ "${chunks:-0}" -lt 3 && "${sqlite_chunks:-0}" -lt 3 ]]; then
  echo "Demo gate failed: expected at least 3 RAG chunks, got chunks=${chunks:-0} sqliteChunks=${sqlite_chunks:-0}" >&2
  exit 2
fi

if [[ "${sources:-0}" -lt 1 ]]; then
  echo "Demo gate failed: chat returned no sources." >&2
  exit 2
fi

cat >"${MANIFEST}" <<EOF
# Evidentia Microvideo Ready Manifest

Fecha UTC: ${STAMP}
Base URL: ${BASE_URL}

## Demo Gate

- Health records: ${records}
- RAG chunks: ${chunks}
- SQLite chunks: ${sqlite_chunks}
- Retrieval mode: ${retrieval_mode}
- Chat sources: ${sources}
- AI status: ver \`$(basename "${ai_json}")\`
- Knowledge bundle: \`$(basename "${export_json}")\`

## Pregunta Probada

\`\`\`
${QUESTION}
\`\`\`

## Secuencia De Grabacion 60-90s

1. Abrir web: \`${BASE_URL}/website.html#web\`
2. Mostrar claim seguro: Vector Knowledge Mirror local-first, no diagnostico.
3. Abrir app: \`${BASE_URL}/index.html#intake\`
4. Mostrar contador de registros demo y pasar a Casos.
5. Abrir Mapa/Entidades y ensenar conexiones.
6. Abrir Chat y repetir la pregunta probada.
7. Mostrar fuentes visibles.
8. Abrir Conectar y descargar o mostrar knowledge bundle.
9. Cerrar con oferta: Piloto Fundador 30 dias, datos autorizados, fuentes y backup.

## Archivos De Evidencia

- \`$(basename "${health_json}")\`
- \`$(basename "${rag_json}")\`
- \`$(basename "${chat_json}")\`
- \`$(basename "${export_json}")\`

## Limite Comercial

Este manifiesto prepara la grabacion. No sustituye el microvideo real ni permite decir que ya esta grabado.
${retrieval_warning}
EOF

echo "${MANIFEST}"
