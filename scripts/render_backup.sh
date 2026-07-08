#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${EVIDENTIA_DATA_DIR:-${ROOT}/data}"
BACKUP_DIR="${EVIDENTIA_BACKUP_DIR:-${DATA_DIR}/backups/render-node}"
RETENTION="${EVIDENTIA_BACKUP_RETENTION:-14}"

export EVIDENTIA_DATA_DIR="${DATA_DIR}"
export EVIDENTIA_BACKUP_DIR="${BACKUP_DIR}"

archive="$("${ROOT}/scripts/evidentia_backup_restore.sh" backup)"
"${ROOT}/scripts/evidentia_backup_restore.sh" verify-restore "${archive}"

python3 - "${BACKUP_DIR}" "${RETENTION}" <<'PY'
from pathlib import Path
import sys

backup_dir = Path(sys.argv[1])
retention = int(sys.argv[2])
archives = sorted(
    backup_dir.glob("evidentia-data-*.tar.gz"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
for stale in archives[retention:]:
    stale.unlink()
print(f"BACKUP_RETENTION_OK kept={min(len(archives), retention)} removed={max(len(archives)-retention, 0)}")
PY

echo "EVIDENTIA_RENDER_BACKUP_OK archive=${archive}"
