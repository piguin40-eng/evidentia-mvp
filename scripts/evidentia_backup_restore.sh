#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT}/data"
BACKUP_DIR="${ROOT}/backups/local-node"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

usage() {
  cat <<'USAGE'
Usage:
  scripts/evidentia_backup_restore.sh backup
  scripts/evidentia_backup_restore.sh inspect <backup.tar.gz>
  scripts/evidentia_backup_restore.sh verify-restore <backup.tar.gz>
  scripts/evidentia_backup_restore.sh restore <backup.tar.gz>

Creates or restores an Evidentia Local Node data backup.
USAGE
}

require_backup_file() {
  local archive="${1:-}"
  if [[ -z "${archive}" || ! -f "${archive}" ]]; then
    echo "Backup archive not found: ${archive:-<missing>}" >&2
    exit 2
  fi
}

backup() {
  mkdir -p "${BACKUP_DIR}"
  if [[ ! -d "${DATA_DIR}" ]]; then
    echo "Data directory not found: ${DATA_DIR}" >&2
    exit 2
  fi

  local archive="${BACKUP_DIR}/evidentia-data-${STAMP}.tar.gz"
  (
    cd "${ROOT}"
    tar \
      --exclude='data/*.log' \
      --exclude='data/**/*.log' \
      -czf "${archive}" \
      data/evidentia.sqlite \
      data/uploads \
      data/rag \
      data/derived \
      data/exports 2>/dev/null
  )
  echo "${archive}"
}

inspect() {
  local archive="${1:-}"
  require_backup_file "${archive}"
  tar -tzf "${archive}" | sed -n '1,120p'
}

verify_restore() {
  local archive="${1:-}"
  require_backup_file "${archive}"

  if ! tar -tzf "${archive}" | grep -q '^data/evidentia\.sqlite$'; then
    echo "Archive does not look like an Evidentia data backup." >&2
    exit 2
  fi

  local staging
  staging="$(mktemp -d "${TMPDIR:-/tmp}/evidentia-restore-check.XXXXXX")"
  trap 'rm -rf "${staging}"' RETURN

  tar -xzf "${archive}" -C "${staging}"

  local restored_data="${staging}/data"
  local restored_db="${restored_data}/evidentia.sqlite"
  local missing=0
  for required in "${restored_db}" "${restored_data}/uploads" "${restored_data}/rag"; do
    if [[ ! -e "${required}" ]]; then
      echo "MISSING ${required#${staging}/}"
      missing=1
    fi
  done
  if [[ "${missing}" -ne 0 ]]; then
    exit 2
  fi

  python3 - "${restored_db}" <<'PY'
import sqlite3
import sys

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
try:
    records = conn.execute("select count(*) from records").fetchone()[0]
    chunks = conn.execute("select count(*) from rag_chunks").fetchone()[0]
    evidence = conn.execute("select count(*) from evidence").fetchone()[0]
finally:
    conn.close()

print(f"RESTORE_CHECK_OK db={db_path}")
print(f"records={records}")
print(f"sqliteChunks={chunks}")
print(f"evidence={evidence}")
if records < 1 or chunks < 1:
    raise SystemExit("Restored backup is not demo-ready: expected at least 1 record and 1 RAG chunk")
PY
}

restore() {
  local archive="${1:-}"
  require_backup_file "${archive}"

  if ! tar -tzf "${archive}" | grep -q '^data/evidentia\.sqlite$'; then
    echo "Archive does not look like an Evidentia data backup." >&2
    exit 2
  fi

  local previous="${ROOT}/data.before-restore-${STAMP}"
  if [[ -d "${DATA_DIR}" ]]; then
    mv "${DATA_DIR}" "${previous}"
    echo "Current data moved to: ${previous}"
  fi

  (
    cd "${ROOT}"
    tar -xzf "${archive}"
  )
  echo "Restored data from: ${archive}"
}

case "${1:-}" in
  backup)
    backup
    ;;
  inspect)
    inspect "${2:-}"
    ;;
  verify-restore)
    verify_restore "${2:-}"
    ;;
  restore)
    restore "${2:-}"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
