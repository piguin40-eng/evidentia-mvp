#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8892}"
OUT_DIR="${OUT_DIR:-${ROOT}/qa/pilot-readiness}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
QUESTION="${QUESTION:-Que conocimiento conecta estetica, laboratorio y aprendizaje?}"
SNAPSHOT="${OUT_DIR}/pilot-readiness-${STAMP}.md"

mkdir -p "${OUT_DIR}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 2
  fi
}

fetch_json() {
  local path="$1"
  curl -fsS --max-time 7 -H 'Accept: application/json' "${BASE_URL}${path}"
}

post_chat() {
  python3 - "$QUESTION" <<'PY' | curl -fsS --max-time 15 -X POST "$BASE_URL/api/chat" \
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

path, dotted = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    value = json.load(handle)
for part in dotted.split("."):
    value = value.get(part) if isinstance(value, dict) else None
print("" if value is None else value)
PY
}

json_len() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path, dotted = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as handle:
    value = json.load(handle)
for part in dotted.split("."):
    value = value.get(part) if isinstance(value, dict) else None
print(len(value or []))
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
ai_enabled="$(json_value "${ai_json}" enabled)"
ai_provider="$(json_value "${ai_json}" provider)"
sources="$(json_len "${chat_json}" sources)"
bundle_records="$(json_len "${export_json}" records)"
bundle_chunks="$(json_len "${export_json}" chunks)"

pass=true
reasons=()
warnings=()

if [[ "${records:-0}" -lt 3 ]]; then
  pass=false
  reasons+=("health devuelve menos de 3 registros")
fi

if [[ "${chunks:-0}" -lt 3 && "${sqlite_chunks:-0}" -lt 3 ]]; then
  pass=false
  reasons+=("RAG devuelve menos de 3 chunks")
fi

if [[ "${chunks:-0}" -lt 3 && "${sqlite_chunks:-0}" -ge 3 ]]; then
  warnings+=("Chroma esta vacio; la demo debe presentarse como modo local con fallback SQLite y fuentes, no como RAG vectorial completo")
fi

if [[ "${sources:-0}" -lt 1 ]]; then
  pass=false
  reasons+=("chat no devuelve fuentes")
fi

if [[ "${bundle_records:-0}" -lt 3 ]]; then
  pass=false
  reasons+=("knowledge bundle devuelve menos de 3 registros")
fi

if [[ "${#reasons[@]}" -eq 0 ]]; then
  reasons+=("sin bloqueos automaticos detectados")
fi

if [[ "${#warnings[@]}" -eq 0 ]]; then
  warnings+=("sin advertencias automaticas")
fi

{
  echo "# Evidentia Pilot Readiness Snapshot"
  echo
  echo "Fecha UTC: ${STAMP}"
  echo "Base URL: ${BASE_URL}"
  echo "Resultado: $([[ "${pass}" == true ]] && echo "PASS" || echo "BLOCKED")"
  echo
  echo "## Estado Del Nodo"
  echo
  echo "- Registros locales: ${records:-0}"
  echo "- Chunks Chroma: ${chunks:-0}"
  echo "- Chunks SQLite: ${sqlite_chunks:-0}"
  if [[ "${chunks:-0}" -ge 3 ]]; then
    echo "- Modo de recuperacion: Chroma vectorial"
  elif [[ "${sqlite_chunks:-0}" -ge 3 ]]; then
    echo "- Modo de recuperacion: fallback SQLite local con fuentes"
  else
    echo "- Modo de recuperacion: no vendible"
  fi
  echo "- Fuentes devueltas por chat: ${sources:-0}"
  echo "- Registros en knowledge bundle: ${bundle_records:-0}"
  echo "- Chunks en knowledge bundle: ${bundle_chunks:-0}"
  echo "- IA externa activada: ${ai_enabled:-unknown}"
  echo "- Proveedor IA: ${ai_provider:-none}"
  echo
  echo "## Pregunta Probada"
  echo
  echo "${QUESTION}"
  echo
  echo "## Puerta Comercial"
  echo
  if [[ "${pass}" == true ]]; then
    echo "- Se puede ensenar como demo tecnica controlada de piloto fundador."
    echo "- No decir que esta listo para operacion clinica ni diagnostico."
    echo "- Mostrar siempre fuentes antes de hablar de valor."
  else
    echo "- No ensenar como demo vendible hasta resolver los bloqueos."
  fi
  for reason in "${reasons[@]}"; do
    echo "- ${reason}"
  done
  echo
  echo "## Advertencias Comerciales"
  echo
  for warning in "${warnings[@]}"; do
    echo "- ${warning}"
  done
  echo
  echo "## Secuencia De Cierre De 10 Minutos"
  echo
  echo "1. Abrir app local y mostrar contador de registros."
  echo "2. Hacer la pregunta probada en Chat."
  echo "3. Abrir al menos una fuente recuperada y explicar trazabilidad."
  echo "4. Exportar o mostrar knowledge bundle."
  echo "5. Cerrar con criterio: si en 30 dias no recupera fuentes utiles, se para."
  echo
  echo "## Archivos De Evidencia"
  echo
  echo "- health: $(basename "${health_json}")"
  echo "- rag: $(basename "${rag_json}")"
  echo "- ai: $(basename "${ai_json}")"
  echo "- chat: $(basename "${chat_json}")"
  echo "- bundle: $(basename "${export_json}")"
} >"${SNAPSHOT}"

echo "${SNAPSHOT}"

if [[ "${pass}" != true ]]; then
  exit 2
fi
