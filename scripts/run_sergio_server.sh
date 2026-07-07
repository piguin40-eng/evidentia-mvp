#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT}/data/sergio-access"
PASSWORD="$(cat "${RUNTIME_DIR}/password.txt")"

cd "${ROOT}"
exec env \
  EVIDENTIA_DATA_DIR="${ROOT}/data/sergio-clean" \
  EVIDENTIA_PORT="8898" \
  EVIDENTIA_HOST="0.0.0.0" \
  EVIDENTIA_AUTH_MODE="cookie" \
  EVIDENTIA_BASIC_AUTH_USER="sergio" \
  EVIDENTIA_BASIC_AUTH_PASSWORD="${PASSWORD}" \
  PYTHONUNBUFFERED="1" \
  .venv/bin/python server.py
