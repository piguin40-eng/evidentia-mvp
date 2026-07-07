#!/usr/bin/env bash
set -euo pipefail
/usr/bin/screen -S evidentia-mobile-tunnel -X quit >/dev/null 2>&1 || true
/usr/bin/screen -S evidentia-mobile-server -X quit >/dev/null 2>&1 || true
/usr/bin/screen -S evidentia-mobile-awake -X quit >/dev/null 2>&1 || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:${EVIDENTIA_MOBILE_PORT:-8897}" >/dev/null 2>&1 || true
lsof -tiTCP:${EVIDENTIA_MOBILE_PORT:-8897} -sTCP:LISTEN | xargs -r kill >/dev/null 2>&1 || true
echo "Evidentia mobile access stopped."
