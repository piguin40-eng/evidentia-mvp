#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT}/data/mobile-access"
ENV_FILE="${RUNTIME_DIR}/mobile-access.env"
SERVER_LOG="${RUNTIME_DIR}/server.log"
TUNNEL_LOG="${RUNTIME_DIR}/cloudflared.log"
CURRENT_URL_FILE="${RUNTIME_DIR}/current-url.env"
CURRENT_URL_TXT="${RUNTIME_DIR}/current_url.txt"
AWAKE_LOG="${RUNTIME_DIR}/awake.log"
KEEP_AWAKE="${EVIDENTIA_KEEP_AWAKE:-0}"
PORT="${EVIDENTIA_MOBILE_PORT:-8897}"
CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-}"
mkdir -p "${RUNTIME_DIR}"

if [[ -z "${CLOUDFLARED_BIN}" ]]; then
  if [[ -x "/opt/homebrew/bin/cloudflared" ]]; then
    CLOUDFLARED_BIN="/opt/homebrew/bin/cloudflared"
  elif [[ -x "/usr/local/bin/cloudflared" ]]; then
    CLOUDFLARED_BIN="/usr/local/bin/cloudflared"
  else
    CLOUDFLARED_BIN="$(command -v cloudflared || true)"
  fi
fi

if [[ -z "${CLOUDFLARED_BIN}" || ! -x "${CLOUDFLARED_BIN}" ]]; then
  echo "cloudflared not found. Install it or set CLOUDFLARED_BIN." >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  USERNAME="miguel"
  PASSWORD="$(openssl rand -base64 24 | tr -d '=+/[:space:]' | cut -c1-24)"
  cat >"${ENV_FILE}" <<EOF
EVIDENTIA_BASIC_AUTH_USER=${USERNAME}
EVIDENTIA_BASIC_AUTH_PASSWORD=${PASSWORD}
EOF
  chmod 600 "${ENV_FILE}"
fi

set -a
source "${ENV_FILE}"
set +a

if [[ -f "${CURRENT_URL_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${CURRENT_URL_FILE}" || true
fi

if [[ "${KEEP_AWAKE}" == "1" ]] && ! /usr/bin/screen -ls 2>/dev/null | grep -q 'evidentia-mobile-awake'; then
  : >"${AWAKE_LOG}"
  /usr/bin/screen -dmS evidentia-mobile-awake bash -lc "/usr/bin/caffeinate -i -m -s >>'${AWAKE_LOG}' 2>&1"
fi

if [[ -n "${EVIDENTIA_MOBILE_URL:-}" ]] \
  && curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1 \
  && pgrep -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null 2>&1 \
  && curl -fsS --max-time 8 "${EVIDENTIA_MOBILE_URL}/api/healthz" >/dev/null 2>&1; then
  printf '%s\n' "${EVIDENTIA_MOBILE_URL}" >"${CURRENT_URL_TXT}"
  chmod 600 "${CURRENT_URL_TXT}"
  cat <<EOF
EVIDENTIA_MOBILE_URL=${EVIDENTIA_MOBILE_URL}
EVIDENTIA_MOBILE_USER=${EVIDENTIA_BASIC_AUTH_USER}
EVIDENTIA_MOBILE_PASSWORD=${EVIDENTIA_BASIC_AUTH_PASSWORD}
EOF
  exit 0
fi

/usr/bin/screen -S evidentia-mobile-server -X quit >/dev/null 2>&1 || true
/usr/bin/screen -S evidentia-mobile-tunnel -X quit >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null 2>&1 || true
lsof -tiTCP:${PORT} -sTCP:LISTEN | xargs -r kill >/dev/null 2>&1 || true

cd "${ROOT}"
: >"${SERVER_LOG}"
: >"${TUNNEL_LOG}"
/usr/bin/screen -dmS evidentia-mobile-server bash -lc "cd '${ROOT}' && EVIDENTIA_PORT='${PORT}' EVIDENTIA_HOST=0.0.0.0 EVIDENTIA_AUTH_MODE=cookie PYTHONUNBUFFERED=1 EVIDENTIA_BASIC_AUTH_USER='${EVIDENTIA_BASIC_AUTH_USER}' EVIDENTIA_BASIC_AUTH_PASSWORD='${EVIDENTIA_BASIC_AUTH_PASSWORD}' .venv/bin/python server.py >>'${SERVER_LOG}' 2>&1"

for _ in {1..40}; do
  if curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! curl -fsS "http://127.0.0.1:${PORT}/api/healthz" >/dev/null 2>&1; then
  echo "Evidentia mobile server did not start. See ${SERVER_LOG}" >&2
  exit 1
fi

/usr/bin/screen -dmS evidentia-mobile-tunnel bash -lc "'${CLOUDFLARED_BIN}' tunnel --url 'http://127.0.0.1:${PORT}' --protocol http2 --no-autoupdate >>'${TUNNEL_LOG}' 2>&1"

URL=""
for _ in {1..80}; do
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

cat >"${CURRENT_URL_FILE}" <<EOF
EVIDENTIA_MOBILE_URL=${URL}
EOF
chmod 600 "${CURRENT_URL_FILE}"
printf '%s\n' "${URL}" >"${CURRENT_URL_TXT}"
chmod 600 "${CURRENT_URL_TXT}"

cat <<EOF
EVIDENTIA_MOBILE_URL=${URL}
EVIDENTIA_MOBILE_USER=${EVIDENTIA_BASIC_AUTH_USER}
EVIDENTIA_MOBILE_PASSWORD=${EVIDENTIA_BASIC_AUTH_PASSWORD}
EOF
