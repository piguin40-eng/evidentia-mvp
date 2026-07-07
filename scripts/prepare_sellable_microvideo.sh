#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8892}"
OUT_DIR="${OUT_DIR:-${ROOT}/qa/microvideo}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
MANIFEST="${OUT_DIR}/microvideo-ready-${STAMP}.md"
ASSET_REPORT="${OUT_DIR}/microvideo-assets-${STAMP}.md"
QUESTION="${QUESTION:-Que conocimiento conecta estetica, laboratorio y aprendizaje?}"
PRIMARY_VIDEO="${PRIMARY_VIDEO:-assets/evidentia/evidentia-llm-ceramic-reference-v3.mp4}"
PRIMARY_POSTER="${PRIMARY_POSTER:-assets/evidentia/evidentia-llm-ceramic-reference-v3-poster.jpg}"

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

primary_video_path="${ROOT}/${PRIMARY_VIDEO}"
primary_poster_path="${ROOT}/${PRIMARY_POSTER}"

if [[ ! -s "${primary_video_path}" ]]; then
  echo "Demo gate failed: primary microvideo asset missing or empty: ${PRIMARY_VIDEO}" >&2
  exit 2
fi

if [[ ! -s "${primary_poster_path}" ]]; then
  echo "Demo gate failed: primary microvideo poster missing or empty: ${PRIMARY_POSTER}" >&2
  exit 2
fi

if command -v ffprobe >/dev/null 2>&1; then
  primary_video_duration="$(ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "${primary_video_path}" | awk '{ printf "%.1f", $1 }')"
  primary_video_resolution="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "${primary_video_path}" | head -n 1)"
else
  primary_video_duration="ffprobe-unavailable"
  primary_video_resolution="ffprobe-unavailable"
fi

{
  echo "# Evidentia Microvideo Asset Inventory"
  echo
  echo "Fecha UTC: ${STAMP}"
  echo
  echo "## Asset Primario Para Venta"
  echo
  echo "- Video: \`${PRIMARY_VIDEO}\`"
  echo "- Poster: \`${PRIMARY_POSTER}\`"
  echo "- Video bytes: $(stat -f "%z" "${primary_video_path}")"
  echo "- Poster bytes: $(stat -f "%z" "${primary_poster_path}")"
  echo "- Duracion: ${primary_video_duration}s"
  echo "- Resolucion: ${primary_video_resolution}"
  echo
  echo "## Inventario MP4/JPG/GIF Disponible"
  echo
  find "${ROOT}/assets/evidentia" -maxdepth 1 -type f \( -name '*.mp4' -o -name '*.jpg' -o -name '*.gif' \) -print | sort | while IFS= read -r asset; do
    rel="${asset#"${ROOT}/"}"
    bytes="$(stat -f "%z" "${asset}")"
    if [[ "${asset}" == *.mp4 && "${primary_video_duration}" != "ffprobe-unavailable" ]]; then
      duration="$(ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "${asset}" | awk '{ printf "%.1f", $1 }')"
      resolution="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "${asset}" | head -n 1)"
      echo "- \`${rel}\` - ${bytes} bytes, ${duration}s, ${resolution}"
    else
      echo "- \`${rel}\` - ${bytes} bytes"
    fi
  done
} >"${ASSET_REPORT}"

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
compact_vector_chunks="$(json_value "${rag_json}" compactVectorChunks)"
chroma_chunks="$(json_value "${rag_json}" chromaChunks)"
sqlite_chunks="$(json_value "${rag_json}" sqliteChunks)"
sources="$(python3 - "${chat_json}" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(len(payload.get("sources") or []))
PY
)"
ai_mode="$(json_value "${ai_json}" mode)"
ai_active="$(json_value "${ai_json}" active)"

if [[ "${ai_mode}" == "rag-local" && ( "${ai_active}" == "False" || "${ai_active}" == "false" ) && "${sources:-0}" -ge 1 ]]; then
  local_resilience="PASS"
  local_resilience_note="Demo preparada en modo local sin IA externa y con fuentes visibles."
else
  local_resilience="WARN"
  local_resilience_note="Antes de grabar, confirmar modo rag-local, IA externa apagada y fuentes visibles."
fi

if [[ "${chunks:-0}" -ge 3 ]]; then
  retrieval_mode="compact vector local"
  retrieval_warning="Sin advertencia automatica de recuperacion."
elif [[ "${sqlite_chunks:-0}" -ge 3 ]]; then
  retrieval_mode="fallback SQLite local con fuentes"
  retrieval_warning="El indice compact vector esta vacio: en el video decir modo local con fuentes, no busqueda vectorial completa."
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
- Compact vector chunks: ${compact_vector_chunks:-${chunks:-0}}
- Chroma chunks: ${chroma_chunks:-not-enabled}
- SQLite chunks: ${sqlite_chunks}
- Retrieval mode: ${retrieval_mode}
- Chat sources: ${sources}
- AI mode: ${ai_mode:-unknown}
- AI externa active: ${ai_active:-unknown}
- Resiliencia local sin API: ${local_resilience}
- Knowledge bundle: \`$(basename "${export_json}")\`
- Asset primario video: \`${PRIMARY_VIDEO}\`
- Asset primario poster: \`${PRIMARY_POSTER}\`
- Video primario: ${primary_video_duration}s, ${primary_video_resolution}
- Inventario assets: \`$(basename "${ASSET_REPORT}")\`

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
- \`$(basename "${ASSET_REPORT}")\`

## Limite Comercial

Este manifiesto prepara la grabacion. No sustituye el microvideo real ni permite decir que ya esta grabado.
${local_resilience_note}
${retrieval_warning}
EOF

echo "${MANIFEST}"
