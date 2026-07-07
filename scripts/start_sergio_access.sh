#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT}/data/sergio-clean"
RUNTIME_DIR="${ROOT}/data/sergio-access"
SERVER_LOG="${RUNTIME_DIR}/server.log"
TUNNEL_LOG="${RUNTIME_DIR}/cloudflared.log"
CURRENT_ENV="${RUNTIME_DIR}/current-url.env"
PORT="8898"
USER_NAME="sergio"

mkdir -p "${DATA_DIR}" "${RUNTIME_DIR}"

if [[ -f "${RUNTIME_DIR}/password.txt" ]]; then
  PASSWORD="$(cat "${RUNTIME_DIR}/password.txt")"
else
  PASSWORD="Sergio$(openssl rand -base64 18 | tr -d '=+/[:space:]' | tr -cd '[:alnum:]' | cut -c1-8)"
  printf '%s\n' "${PASSWORD}" >"${RUNTIME_DIR}/password.txt"
  chmod 600 "${RUNTIME_DIR}/password.txt"
fi

/usr/bin/screen -S evidentia-sergio-server -X quit >/dev/null 2>&1 || true
/usr/bin/screen -S evidentia-sergio-tunnel -X quit >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null 2>&1 || true
lsof -tiTCP:"${PORT}" -sTCP:LISTEN | xargs -r kill >/dev/null 2>&1 || true

: >"${SERVER_LOG}"
: >"${TUNNEL_LOG}"

/usr/bin/screen -dmS evidentia-sergio-server bash -lc \
  "cd '${ROOT}' && EVIDENTIA_DATA_DIR='${DATA_DIR}' EVIDENTIA_PORT='${PORT}' EVIDENTIA_HOST=0.0.0.0 EVIDENTIA_AUTH_MODE=cookie EVIDENTIA_BASIC_AUTH_USER='${USER_NAME}' EVIDENTIA_BASIC_AUTH_PASSWORD='${PASSWORD}' PYTHONUNBUFFERED=1 .venv/bin/python server.py >>'${SERVER_LOG}' 2>&1"

for _ in {1..60}; do
  if curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
  echo "Sergio Evidentia server did not start. See ${SERVER_LOG}" >&2
  exit 1
fi

CLOUDFLARED_BIN="/opt/homebrew/bin/cloudflared"
if [[ ! -x "${CLOUDFLARED_BIN}" ]]; then
  CLOUDFLARED_BIN="$(command -v cloudflared)"
fi

/usr/bin/screen -dmS evidentia-sergio-tunnel bash -lc \
  "'${CLOUDFLARED_BIN}' tunnel --url 'http://127.0.0.1:${PORT}' --protocol http2 --no-autoupdate >>'${TUNNEL_LOG}' 2>&1"

URL=""
for _ in {1..100}; do
  URL="$(grep -Eo 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "${TUNNEL_LOG}" | tail -1 || true)"
  if [[ -n "${URL}" ]]; then
    break
  fi
  sleep 0.25
done

if [[ -z "${URL}" ]]; then
  echo "Cloudflare tunnel did not return a URL. See ${TUNNEL_LOG}" >&2
  exit 1
fi

cat >"${CURRENT_ENV}" <<EOF
EVIDENTIA_SERGIO_URL=${URL}
EVIDENTIA_SERGIO_USER=${USER_NAME}
EVIDENTIA_SERGIO_PASSWORD=${PASSWORD}
EVIDENTIA_SERGIO_DATA_DIR=${DATA_DIR}
EOF
chmod 600 "${CURRENT_ENV}"

cat "${CURRENT_ENV}"
