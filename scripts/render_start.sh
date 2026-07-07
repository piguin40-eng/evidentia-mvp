#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

mkdir -p data

if [[ "${EVIDENTIA_RESTORE_SEED:-false}" == "true" && ! -f data/evidentia.sqlite && -f deploy/evidentia-data-seed.tar.gz ]]; then
  echo "Restoring Evidentia seed data into persistent disk..."
  tar -xzf deploy/evidentia-data-seed.tar.gz
fi

mkdir -p data/uploads data/rag/vector data/rag/chroma data/exports data/derived

exec python server.py
