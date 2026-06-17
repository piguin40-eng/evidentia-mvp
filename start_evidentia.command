#!/bin/zsh
cd "$(dirname "$0")"
mkdir -p data/uploads data/rag/chroma data/exports data/audit
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi
if [ ! -x ".venv/bin/python" ]; then
  echo "Creando entorno local Evidentia..."
  uv venv .venv --python 3.12
  uv pip install --python .venv/bin/python chromadb pypdf pillow
fi
echo "Evidentia Local Node"
echo "Abre http://127.0.0.1:8892 en este ordenador."
.venv/bin/python server.py
