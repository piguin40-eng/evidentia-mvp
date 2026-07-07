#!/usr/bin/env python3
"""Rebuild Evidentia's compact local vector index from SQLite RAG chunks."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "evidentia.sqlite"
VECTOR_DIR = ROOT / "data" / "rag" / "vector"
MATRIX_PATH = VECTOR_DIR / "embeddings.npy"
IDS_PATH = VECTOR_DIR / "chunk_ids.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild data/rag/vector from the rag_chunks SQLite mirror."
    )
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path.")
    parser.add_argument("--batch-size", type=int, default=128, help="Embedding batch size.")
    parser.add_argument("--limit", type=int, default=0, help="Optional chunk limit for smoke tests.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing files.")
    parser.add_argument("--check-deps", action="store_true", help="Validate vector dependencies without writing files.")
    return parser.parse_args()


def load_chunks(db_path: Path, limit: int) -> list[tuple[str, str]]:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    query = """
        SELECT id, text
        FROM rag_chunks
        WHERE trim(text) != ''
        ORDER BY created_at ASC, chunk_index ASC, id ASC
    """
    params: tuple[int, ...] = ()
    if limit > 0:
        query += " LIMIT ?"
        params = (limit,)

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(query, params).fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser().resolve()
    chunks = load_chunks(db_path, args.limit)

    if not chunks:
        print(json.dumps({
            "ok": False,
            "error": "no_rag_chunks",
            "db": str(db_path),
            "message": "No rag_chunks rows found to index.",
        }, ensure_ascii=False))
        return 2

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dryRun": True,
            "db": str(db_path),
            "chunks": len(chunks),
            "targetMatrix": str(MATRIX_PATH),
            "targetIds": str(IDS_PATH),
        }, ensure_ascii=False))
        return 0

    try:
        import numpy as np
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    except Exception as exc:
        venv_python = ROOT / ".venv" / "bin" / "python"
        if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
            os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])
        print(json.dumps({
            "ok": False,
            "error": "missing_vector_dependencies",
            "db": str(db_path),
            "chunks": len(chunks),
            "message": "Install requirements before rebuilding: python3 -m pip install -r requirements.txt",
            "detail": str(exc),
        }, ensure_ascii=False))
        return 2

    if args.check_deps:
        print(json.dumps({
            "ok": True,
            "checkDeps": True,
            "python": sys.executable,
            "chunks": len(chunks),
            "numpy": getattr(np, "__version__", "unknown"),
            "embedder": DefaultEmbeddingFunction.__name__,
        }, ensure_ascii=False))
        return 0

    embedder = DefaultEmbeddingFunction()
    ids: list[str] = []
    vectors = []

    for start in range(0, len(chunks), args.batch_size):
        batch = chunks[start:start + args.batch_size]
        batch_ids = [chunk_id for chunk_id, _text in batch]
        batch_texts = [text for _chunk_id, text in batch]
        batch_vectors = np.asarray(embedder(batch_texts), dtype="float32")
        norms = np.linalg.norm(batch_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors.append(batch_vectors / norms)
        ids.extend(batch_ids)

    matrix = np.vstack(vectors).astype("float32")
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    tmp_matrix = MATRIX_PATH.with_suffix(".npy.tmp")
    tmp_ids = IDS_PATH.with_suffix(".json.tmp")
    with tmp_matrix.open("wb") as handle:
        np.save(handle, matrix)
    tmp_ids.write_text(json.dumps(ids, ensure_ascii=False), encoding="utf-8")
    tmp_matrix.replace(MATRIX_PATH)
    tmp_ids.replace(IDS_PATH)

    print(json.dumps({
        "ok": True,
        "db": str(db_path),
        "chunks": len(ids),
        "dimensions": int(matrix.shape[1]),
        "matrix": str(MATRIX_PATH),
        "ids": str(IDS_PATH),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
