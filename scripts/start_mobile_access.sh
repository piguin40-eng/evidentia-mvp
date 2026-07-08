#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT}/data/mobile-access"
ENV_FILE="${RUNTIME_DIR}/mobile-access.env"
SERVER_LOG="${RUNTIME_DIR}/server.log"
CURRENT_URL_FILE="${RUNTIME_DIR}/current-url.env"
CURRENT_URL_TXT="${RUNTIME_DIR}/current_url.txt"
AWAKE_LOG="${RUNTIME_DIR}/awake.log"
KEEP_AWAKE="${EVIDENTIA_KEEP_AWAKE:-0}"
PORT="${EVIDENTIA_MOBILE_PORT:-8897}"

mkdir -p "${RUNTIME_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  USERNAME="miguel"
  PASSWORD="$(openssl rand -base64 24 | tr -d '=+/[:space:]' | cut -c1-24)"
  {
    printf 'EVIDENTIA_BASIC_AUTH_USER=%s\n' "${USERNAME}"
    printf 'EVIDENTIA_BASIC_AUTH_PASSWORD=%s\n' "${PASSWORD}"
  } >"${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
fi

set -a
source "${ENV_FILE}"
set +a

if [[ "${KEEP_AWAKE}" == "1" ]] && ! /usr/bin/screen -ls 2>/dev/null | grep -q 'evidentia-mobile-awake'; then
  : >"${AWAKE_LOG}"
  /usr/bin/screen -dmS evidentia-mobile-awake bash -lc "/usr/bin/caffeinate -i -m -s >>'${AWAKE_LOG}' 2>&1"
fi

# Miguel explicitly rejected temporary public links. Mobile access is LAN-only:
# same WiFi, cookie login, local data, no Cloudflare/ngrok tunnel.
/usr/bin/screen -S evidentia-mobile-tunnel -X quit >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null 2>&1 || true

if curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
  RUNNING=1
else
  RUNNING=0
fi

if [[ "${RUNNING}" != "1" ]]; then
  /usr/bin/screen -S evidentia-mobile-server -X quit >/dev/null 2>&1 || true
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN | xargs -r kill >/dev/null 2>&1 || true
  : >"${SERVER_LOG}"
  /usr/bin/screen -dmS evidentia-mobile-server bash -lc "cd '${ROOT}' && EVIDENTIA_PORT='${PORT}' EVIDENTIA_HOST=0.0.0.0 EVIDENTIA_AUTH_MODE=cookie PYTHONUNBUFFERED=1 EVIDENTIA_BASIC_AUTH_USER='${EVIDENTIA_BASIC_AUTH_USER}' EVIDENTIA_BASIC_AUTH_PASSWORD='${EVIDENTIA_BASIC_AUTH_PASSWORD}' .venv/bin/python server.py >>'${SERVER_LOG}' 2>&1"

  for _ in {1..40}; do
    if curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done
fi

if ! curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
  echo "Evidentia LAN mobile server did not start. See ${SERVER_LOG}" >&2
  exit 1
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
LOCAL_HOSTNAME="$(scutil --get LocalHostName 2>/dev/null || hostname -s 2>/dev/null || true)"
if [[ -n "${LOCAL_HOSTNAME}" ]]; then
  LAN_HOST_URL="http://${LOCAL_HOSTNAME}.local:${PORT}/"
else
  LAN_HOST_URL=""
fi
if [[ -n "${LAN_IP}" ]]; then
  LAN_IP_URL="http://${LAN_IP}:${PORT}/"
else
  LAN_IP_URL=""
fi

PRIMARY_URL="${LAN_HOST_URL:-${LAN_IP_URL}}"
if [[ -z "${PRIMARY_URL}" ]]; then
  PRIMARY_URL="http://127.0.0.1:${PORT}/"
fi

{
  printf 'EVIDENTIA_MOBILE_URL=%s\n' "${PRIMARY_URL}"
  printf 'EVIDENTIA_MOBILE_LAN_IP_URL=%s\n' "${LAN_IP_URL}"
  printf 'EVIDENTIA_MOBILE_LAN_HOST_URL=%s\n' "${LAN_HOST_URL}"
} >"${CURRENT_URL_FILE}"
chmod 600 "${CURRENT_URL_FILE}"
printf '%s\n' "${PRIMARY_URL}" >"${CURRENT_URL_TXT}"
chmod 600 "${CURRENT_URL_TXT}"

cat <<EOF
EVIDENTIA_MOBILE_URL=${PRIMARY_URL}
EVIDENTIA_MOBILE_LAN_IP_URL=${LAN_IP_URL}
EVIDENTIA_MOBILE_LAN_HOST_URL=${LAN_HOST_URL}
EVIDENTIA_MOBILE_USER=${EVIDENTIA_BASIC_AUTH_USER}
EVIDENTIA_MOBILE_PASSWORD=${EVIDENTIA_BASIC_AUTH_PASSWORD}
EVIDENTIA_MOBILE_SCOPE=LAN_ONLY
EOF
