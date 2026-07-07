#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8892}"
OUT_DIR="${OUT_DIR:-${ROOT}/qa/microdemo-preflight}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${OUT_DIR}/microdemo-preflight-${STAMP}.md"
QUESTION="${QUESTION:-Que conocimiento conecta estetica, laboratorio y aprendizaje?}"
CANDIDATE_NAME="${CANDIDATE_NAME:-}"
MIGUEL_APPROVAL="${MIGUEL_APPROVAL:-no}"
DEMO_DATE="${DEMO_DATE:-}"

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
  python3 - "${QUESTION}" <<'PY' | curl -fsS --max-time 10 -X POST "${BASE_URL}/api/chat" \
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

add_score() {
  local condition="$1"
  local pass_points="$2"
  local warn_points="$3"
  if [[ "${condition}" == "pass" ]]; then
    SCORE=$((SCORE + pass_points))
  elif [[ "${condition}" == "warn" ]]; then
    SCORE=$((SCORE + warn_points))
  fi
}

need curl
need python3

health_json="${OUT_DIR}/health-${STAMP}.json"
rag_json="${OUT_DIR}/rag-${STAMP}.json"
ai_json="${OUT_DIR}/ai-${STAMP}.json"
chat_json="${OUT_DIR}/chat-${STAMP}.json"

fetch_json /api/health >"${health_json}"
fetch_json /api/rag/stats >"${rag_json}"
fetch_json /api/ai/status >"${ai_json}"
post_chat >"${chat_json}"

records="$(json_value "${health_json}" records)"
chunks="$(json_value "${rag_json}" chunks)"
compact_vector_chunks="$(json_value "${rag_json}" compactVectorChunks)"
sqlite_chunks="$(json_value "${rag_json}" sqliteChunks)"
ai_mode="$(json_value "${ai_json}" mode)"
ai_active="$(json_value "${ai_json}" active)"
sources="$(python3 - "${chat_json}" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(len(payload.get("sources") or []))
PY
)"

SCORE=0

candidate_status="fail"
if [[ -n "${CANDIDATE_NAME}" && "${MIGUEL_APPROVAL}" == "yes" && -n "${DEMO_DATE}" ]]; then
  candidate_status="pass"
elif [[ -n "${CANDIDATE_NAME}" || "${MIGUEL_APPROVAL}" == "yes" || -n "${DEMO_DATE}" ]]; then
  candidate_status="warn"
fi
add_score "${candidate_status}" 2 1

data_status="warn"
if rg -qi "ficticios|anonimizados|autorizados" "${ROOT}/PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md" "${ROOT}/MICRODEMO_ACCEPTANCE_GATE.md"; then
  data_status="pass"
fi
add_score "${data_status}" 2 1

node_status="fail"
if [[ "${records:-0}" -ge 3 && ( "${chunks:-0}" -ge 3 || "${sqlite_chunks:-0}" -ge 3 ) && "${sources:-0}" -ge 1 ]]; then
  node_status="pass"
elif [[ "${records:-0}" -ge 3 || "${sources:-0}" -ge 1 ]]; then
  node_status="warn"
fi
add_score "${node_status}" 2 1

value_status="warn"
if [[ "${QUESTION}" != "Que conocimiento conecta estetica, laboratorio y aprendizaje?" ]]; then
  value_status="pass"
fi
add_score "${value_status}" 2 1

trust_status="fail"
if rg -qi "no diagnostica|no software medico|decision humana|fuentes visibles|local-first" \
  "${ROOT}/SALES_ONE_PAGER.md" \
  "${ROOT}/PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md" \
  "${ROOT}/MICRODEMO_ACCEPTANCE_GATE.md"; then
  trust_status="pass"
fi
add_score "${trust_status}" 2 1

close_status="warn"
if rg -q "500 EUR setup \+ 50 EUR/mes|500 EUR setup|50 EUR/mes" "${ROOT}/SALES_ONE_PAGER.md" "${ROOT}/PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md"; then
  close_status="pass"
fi
add_score "${close_status}" 2 1

local_status="fail"
if [[ "${ai_active}" == "False" || "${ai_active}" == "false" ]] && [[ "${ai_mode}" == "rag-local" ]] && [[ "${sources:-0}" -ge 1 ]]; then
  local_status="pass"
elif [[ "${sources:-0}" -ge 1 ]]; then
  local_status="warn"
fi
add_score "${local_status}" 2 1

if [[ "${SCORE}" -ge 12 && "${candidate_status}" == "pass" ]]; then
  SEMAPHORE="VERDE"
  DECISION="Se puede pedir decision de piloto fundador si el candidato entiende limites y datos."
elif [[ "${SCORE}" -ge 8 ]]; then
  SEMAPHORE="AMARILLO"
  DECISION="Demo tecnica controlada; no cerrar piloto pagado sin resolver los huecos marcados."
else
  SEMAPHORE="ROJO"
  DECISION="No ensenar como vendible. Resolver bloqueos antes de pedir piloto."
fi

cat >"${REPORT}" <<EOF
# Evidentia Microdemo Preflight Gate

Fecha UTC: ${STAMP}
Base URL: ${BASE_URL}
Resultado: ${SEMAPHORE}
Score microdemo: ${SCORE}/14

## Decision

${DECISION}

## Entradas Comerciales

- Candidato: ${CANDIDATE_NAME:-pendiente}
- Aprobacion explicita de Miguel: ${MIGUEL_APPROVAL}
- Fecha propuesta: ${DEMO_DATE:-pendiente}
- Pregunta probada: ${QUESTION}

## Evidencia Tecnica

- Records: ${records:-0}
- Chunks: ${chunks:-0}
- Compact vector chunks: ${compact_vector_chunks:-0}
- SQLite chunks: ${sqlite_chunks:-0}
- Chat sources: ${sources:-0}
- AI mode: ${ai_mode:-unknown}
- AI externa active: ${ai_active:-unknown}

## Bloques

| Bloque | Estado | Nota |
|---|---|---|
| Candidato | ${candidate_status} | Requiere nombre, permiso explicito y fecha para verde. |
| Datos | ${data_status} | Deben ser ficticios, anonimizados o autorizados. |
| Nodo | ${node_status} | Health + RAG + chat con fuentes. |
| Valor | ${value_status} | Verde cuando la pregunta refleja dolor real del candidato. |
| Confianza | ${trust_status} | Limites: no diagnostico, fuentes, decision humana, local-first. |
| Cierre | ${close_status} | Oferta fundador y decision final preparadas. |
| Resiliencia local | ${local_status} | Verde cuando IA externa esta apagada, modo rag-local y chat devuelve fuentes. |

## Archivos De Evidencia

- $(basename "${health_json}")
- $(basename "${rag_json}")
- $(basename "${ai_json}")
- $(basename "${chat_json}")

## Proxima Accion

Completar CANDIDATE_NAME, MIGUEL_APPROVAL=yes y DEMO_DATE al ejecutar este script. Si sigue en AMARILLO, usarlo solo para demo controlada, no para cierre pagado.
EOF

echo "${REPORT}"
echo "${SEMAPHORE} ${SCORE}/14"
