#!/usr/bin/env python3
"""
Evidentia local product backbone.

Serves the frontend and persists records, entities, relations, and evidence in
SQLite. It intentionally uses the Python standard library so the first product
loop can run on Miguel's Mac without dependency setup.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlrequest
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "evidentia.sqlite"
UPLOAD_DIR = DATA_DIR / "uploads"
RAG_DIR = DATA_DIR / "rag" / "chroma"
VISION_DIR = DATA_DIR / "vision"
CHROMA_COLLECTION = "evidentia_knowledge"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


ENTITY_RULES = [
    ("discipline", "Ortodoncia", re.compile(r"ortodoncia|alineador|bracket|oclusion|oclusión|maloclusion|maloclusión", re.I)),
    ("discipline", "Rehabilitacion", re.compile(r"rehabilitacion|rehabilitación|protesis|prótesis|implante|implantologia|implantología", re.I)),
    ("discipline", "Estetica dental", re.compile(r"estetica|estética|sonrisa|carilla|veneer|mockup|mocap", re.I)),
    ("discipline", "Periodoncia", re.compile(r"periodoncia|encia|encía|periodontal|gingival", re.I)),
    ("asset", "Fotografias", re.compile(r"foto|fotografia|fotografía|imagen|polarizada", re.I)),
    ("asset", "Video", re.compile(r"video|vídeo|grabacion|grabación", re.I)),
    ("asset", "PDF o documento", re.compile(r"pdf|documento|informe|consentimiento", re.I)),
    ("asset", "Escaneo o archivo 3D", re.compile(r"stl|scan|escaneo|intraoral|cbct|dicom", re.I)),
    ("knowledge", "Nota de conocimiento", re.compile(r"nota|transcripcion|transcripción|decision|decisión|criterio|observacion|observación", re.I)),
    ("knowledge", "Protocolo o aprendizaje", re.compile(r"protocolo|aprendizaje|leccion|lección|recordar|conocimiento", re.I)),
    ("measurement", "CIELAB", re.compile(r"cielab|l\*|a\*|b\*|delta e|de00", re.I)),
    ("measurement", "Medicion", re.compile(r"medicion|medición|medida|espesor|grosor|\d+(?:[.,]\d+)?\s*mm", re.I)),
    ("outcome", "Resultado o seguimiento", re.compile(r"resultado|exito|éxito|fracaso|estable|seguimiento|dolor|problema|revision|revisión", re.I)),
    ("evidence", "Evidencia asociada", re.compile(r"evidencia|radiografia|radiografía|scan|pdf|documento|foto|video", re.I)),
]


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    VISION_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            capture_date TEXT,
            domain TEXT NOT NULL,
            record_type TEXT NOT NULL,
            patient_code TEXT NOT NULL,
            has_private_identity INTEGER NOT NULL DEFAULT 0,
            operator TEXT,
            notes TEXT NOT NULL,
            source_channel TEXT NOT NULL DEFAULT 'web',
            status TEXT NOT NULL DEFAULT 'structured'
        );

        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            source TEXT NOT NULL DEFAULT 'rule',
            UNIQUE(record_id, type, label)
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            mime_type TEXT,
            size INTEGER,
            storage_uri TEXT,
            sha256 TEXT
        );

        CREATE TABLE IF NOT EXISTS relations (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL,
            confidence REAL NOT NULL,
            evidence_id TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
            record_id UNINDEXED,
            notes,
            domain,
            record_type,
            operator,
            patient_code
        );

        CREATE TABLE IF NOT EXISTS rag_chunks (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            source_name TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return cleaned or "archivo"


def get_chroma_collection():
    try:
        import chromadb
    except Exception as exc:
        raise RuntimeError("ChromaDB no esta instalado en el entorno de Evidentia") from exc

    client = chromadb.PersistentClient(path=str(RAG_DIR))
    return client.get_or_create_collection(name=CHROMA_COLLECTION)


def chunk_text(text: str, size: int = 900, overlap: int = 140) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        chunk = clean[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += max(1, size - overlap)
    return chunks


def extract_text_from_path(path: Path, mime_type: str | None = None) -> str:
    suffix = path.suffix.lower()
    mime_type = mime_type or mimetypes.guess_type(path.name)[0] or ""
    if suffix in {".txt", ".md", ".csv", ".json", ".html", ".htm", ".xml"} or mime_type.startswith("text/"):
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf" or mime_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except Exception:
            return "PDF guardado sin extraccion de texto porque pypdf no esta disponible: " + path.name
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if mime_type.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}:
        return analyze_image(path)
    if mime_type.startswith("video/") or suffix in {".mp4", ".mov", ".m4v"}:
        return analyze_video(path)
    return "Archivo guardado para el mapa de conocimiento: " + path.name


def analyze_image(path: Path, label: str | None = None) -> str:
    try:
        from PIL import Image, ImageStat, ImageFilter
    except Exception:
        return "Imagen guardada para el mapa de conocimiento: " + path.name + ". Pillow no disponible para analisis visual local."

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            width, height = image.size
            stat = ImageStat.Stat(image)
            mean = stat.mean
            gray = image.convert("L")
            brightness = ImageStat.Stat(gray).mean[0]
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_strength = ImageStat.Stat(edges).mean[0]
            r, g, b = mean
            warmth = r - b
            colorfulness = max(mean) - min(mean)
            orientation = "horizontal" if width > height else "vertical" if height > width else "cuadrada"
            return (
                "Analisis visual local"
                + (f" de {label}" if label else "")
                + f": imagen {path.name}; dimensiones {width}x{height}px; orientacion {orientation}; "
                + f"luminosidad media {brightness:.1f}/255; color medio RGB {r:.1f}, {g:.1f}, {b:.1f}; "
                + f"calidez rojo-azul {warmth:.1f}; variacion cromatica {colorfulness:.1f}; detalle/bordes {edge_strength:.1f}. "
                + "Contenido listo para busqueda visual basica en Chroma. Interpretacion semantica avanzada pendiente de modelo especializado."
            )
    except Exception as exc:
        return f"Imagen guardada para el mapa de conocimiento: {path.name}. Error en analisis visual local: {exc}"


def analyze_video(path: Path) -> str:
    frame_dir = VISION_DIR / stable_id(path.name, str(path.stat().st_size))
    frame_dir.mkdir(parents=True, exist_ok=True)
    duration = "desconocida"
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        if probe.stdout.strip():
            duration = f"{float(probe.stdout.strip()):.1f}s"
    except Exception:
        pass

    frame_paths: list[Path] = []
    for second in (1, 3, 6):
        target = frame_dir / f"frame_{second}.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(second), "-i", str(path), "-frames:v", "1", str(target)],
                timeout=30,
                check=False,
            )
            if target.exists() and target.stat().st_size > 0:
                frame_paths.append(target)
        except Exception:
            continue

    frame_analysis = [analyze_image(frame, label=f"frame {idx + 1}") for idx, frame in enumerate(frame_paths)]
    if not frame_analysis:
        frame_analysis.append("No se pudieron extraer frames analizables con ffmpeg.")
    return (
        f"Analisis visual local de video: {path.name}; duracion {duration}; frames extraidos {len(frame_paths)}. "
        + " ".join(frame_analysis)
        + " Transcripcion de audio y vision semantica avanzada pendientes de activar."
    )


def index_record_in_rag(record: dict) -> int:
    collection = get_chroma_collection()
    chunks_payload: list[tuple[str, str, str]] = []
    chunks_payload.append(("nota del caso", "record_notes", record["notes"]))

    for file_item in record.get("files", []):
        storage_uri = file_item.get("storageUri")
        name = str(file_item.get("name") or "archivo")
        if not storage_uri:
            continue
        path = (ROOT / storage_uri).resolve()
        if ROOT not in path.parents and path != ROOT:
            continue
        if path.exists():
            chunks_payload.append((name, "file_text", extract_text_from_path(path, file_item.get("type"))))

    ids: list[str] = []
    docs: list[str] = []
    metadatas: list[dict] = []
    rows: list[tuple[str, str, str, int, str, str]] = []
    created_at = now_iso()
    for source_name, source_type, text in chunks_payload:
        for index, chunk in enumerate(chunk_text(text)):
            chunk_id = stable_id(record["id"], source_name, str(index), chunk[:80])
            ids.append(chunk_id)
            docs.append(chunk)
            metadatas.append({
                "record_id": record["id"],
                "patient_code": record["patientCode"],
                "domain": record["domain"],
                "record_type": record["recordType"],
                "source_name": source_name,
                "source_type": source_type,
                "chunk_index": index,
            })
            rows.append((chunk_id, record["id"], source_name, index, chunk, created_at))

    with connect() as conn:
        conn.execute("DELETE FROM rag_chunks WHERE record_id = ?", (record["id"],))
        conn.executemany(
            "INSERT OR REPLACE INTO rag_chunks (id, record_id, source_name, chunk_index, text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )

    try:
        collection.delete(where={"record_id": record["id"]})
    except Exception:
        pass
    if ids:
        collection.add(ids=ids, documents=docs, metadatas=metadatas)
    return len(ids)


def rag_stats() -> dict:
    stats = {"path": str(RAG_DIR), "collection": CHROMA_COLLECTION, "chunks": 0, "backend": "chroma"}
    try:
        stats["chunks"] = get_chroma_collection().count()
    except Exception as exc:
        stats["backend"] = "unavailable"
        stats["error"] = str(exc)
    with connect() as conn:
        stats["sqliteChunks"] = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
    return stats


def ai_status() -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return {
        "provider": "openai",
        "active": bool(api_key),
        "model": OPENAI_MODEL if api_key else None,
        "mode": "openai" if api_key else "rag-local",
        "message": "OpenAI activo" if api_key else "OpenAI no configurado: define OPENAI_API_KEY para activar sintesis IA",
    }


def openai_synthesize(question: str, chunks: list[dict]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or not chunks:
        return None

    context = "\n\n".join(
        f"FUENTE {index + 1} | {chunk['metadata'].get('patient_code', 'registro')} | {chunk['metadata'].get('source_name', 'fuente')}\n{chunk['text']}"
        for index, chunk in enumerate(chunks[:8])
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el asistente interno de Evidentia, una plataforma para crear el espejo vectorial del conocimiento de una persona, equipo, centro u organizacion. "
                    "Responde solo con evidencia del contexto recuperado. No inventes datos, relaciones ni conclusiones. "
                    "Si la evidencia es insuficiente, dilo. Cita las fuentes por numero."
                ),
            },
            {
                "role": "user",
                "content": f"Pregunta: {question}\n\nContexto recuperado desde Chroma:\n{context}",
            },
        ],
        "temperature": 0.2,
    }
    req = urlrequest.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return "OpenAI configurado, pero la llamada fallo. Respuesta RAG local mantenida. Error: " + str(exc)


def query_rag(question: str, n_results: int = 6) -> dict:
    question = question.strip()
    if not question:
        return {"answer": "Haz una pregunta sobre el conocimiento guardado.", "sources": [], "chunks": []}
    collection = get_chroma_collection()
    result = collection.query(query_texts=[question], n_results=n_results)
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0] if result.get("distances") else [None] * len(ids)
    chunks = []
    record_ids = []
    for chunk_id, doc, metadata, distance in zip(ids, docs, metadatas, distances):
        metadata = metadata or {}
        record_id = metadata.get("record_id")
        if record_id and record_id not in record_ids:
            record_ids.append(record_id)
        chunks.append({
            "id": chunk_id,
            "text": doc,
            "metadata": metadata,
            "distance": distance,
        })

    sources = records_by_ids(record_ids)
    if not chunks:
        return {
            "answer": "No encuentro todavia contenido vectorizado para esa pregunta. Arrastra una transcripcion, PDF, nota o archivo y guardalo en el mapa.",
            "sources": [],
            "chunks": [],
        }

    top_lines = []
    for index, chunk in enumerate(chunks[:3], 1):
        metadata = chunk["metadata"]
        top_lines.append(f"{index}. {metadata.get('patient_code', 'registro')} · {metadata.get('source_name', 'fuente')}: {chunk['text'][:260]}")
    local_answer = (
        f"He buscado en la base vectorial Chroma y encontre {len(chunks)} fragmentos relevantes.\n\n"
        + "\n".join(top_lines)
        + "\n\nRespuesta prudente: usa estas fuentes como memoria recuperada. Para una conclusion accionable, una persona cualificada debe validar el contexto completo."
    )
    synthesized = openai_synthesize(question, chunks)
    answer = synthesized or local_answer
    return {"answer": answer, "sources": sources, "chunks": chunks, "ai": ai_status()}


def anonymize(raw: str) -> str:
    if not raw:
        return "CASE-" + stable_id(now_iso())[:8].upper()
    return "PAT-" + hashlib.sha256(raw.strip().lower().encode("utf-8")).hexdigest()[:10].upper()


def extract_entities(text: str) -> list[dict]:
    entities: list[dict] = []
    for entity_type, label, pattern in ENTITY_RULES:
        if pattern.search(text):
            entities.append({"type": entity_type, "label": label, "confidence": 0.74, "source": "rule"})

    for shade in re.findall(r"\b(?:A|B|C|D)[1-4]\b|\bBL[1-4]\b|\bND[1-9]\b", text, flags=re.I):
        entities.append({"type": "measurement", "label": f"Color {shade.upper()}", "confidence": 0.82, "source": "regex"})

    seen = set()
    unique = []
    for entity in entities:
        key = (entity["type"], entity["label"])
        if key not in seen:
            seen.add(key)
            unique.append(entity)
    return unique


def relation_for(entity_type: str) -> str:
    return {
        "discipline": "clasifica_area",
        "asset": "incluye_activo",
        "knowledge": "contiene_conocimiento",
        "material": "usa_o_menciona_material",
        "treatment": "describe_tratamiento",
        "measurement": "contiene_medicion",
        "outcome": "aporta_resultado",
        "evidence": "aporta_evidencia",
    }.get(entity_type, "relacionado_con")


def normalize_record(payload: dict) -> dict:
    notes = str(payload.get("notes") or "").strip()
    if not notes:
        raise ValueError("notes is required")

    patient_code = str(payload.get("patientCode") or "").strip()
    patient_raw = str(payload.get("patient") or "").strip()
    if not patient_code:
        patient_code = anonymize(patient_raw)

    record_id = str(payload.get("id") or stable_id(patient_code, notes, now_iso()))
    entities = payload.get("entities") or extract_entities(notes)
    files = payload.get("files") or []
    created_at = str(payload.get("createdAt") or now_iso())

    return {
        "id": record_id,
        "createdAt": created_at,
        "date": str(payload.get("date") or created_at[:10]),
        "domain": str(payload.get("domain") or "Conocimiento general"),
        "recordType": str(payload.get("recordType") or "Transcripcion"),
        "patientCode": patient_code,
        "hasPrivateIdentity": bool(payload.get("hasPrivateIdentity") or patient_raw),
        "operator": str(payload.get("operator") or "Sin responsable"),
        "notes": notes,
        "files": files,
        "entities": entities,
        "graph": build_graph(patient_code, entities, files),
    }


def build_graph(patient_code: str, entities: list[dict], files: list[dict]) -> list[dict]:
    graph = [{"type": "identity", "label": patient_code, "relation": "caso_anonimizado"}]
    for entity in entities:
        graph.append({"type": entity["type"], "label": entity["label"], "relation": relation_for(entity["type"])})
    for file_item in files:
        graph.append({"type": "evidence", "label": str(file_item.get("name") or "archivo"), "relation": "evidencia_asociada"})
    return graph


def save_record(record: dict) -> dict:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO records
            (id, created_at, capture_date, domain, record_type, patient_code, has_private_identity, operator, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["createdAt"],
                record["date"],
                record["domain"],
                record["recordType"],
                record["patientCode"],
                int(record["hasPrivateIdentity"]),
                record["operator"],
                record["notes"],
            ),
        )
        conn.execute("DELETE FROM entities WHERE record_id = ?", (record["id"],))
        conn.execute("DELETE FROM evidence WHERE record_id = ?", (record["id"],))
        conn.execute("DELETE FROM relations WHERE record_id = ?", (record["id"],))
        conn.execute("DELETE FROM records_fts WHERE record_id = ?", (record["id"],))

        for entity in record["entities"]:
            entity_id = stable_id(record["id"], entity["type"], entity["label"])
            conn.execute(
                "INSERT OR IGNORE INTO entities (id, record_id, type, label, confidence, source) VALUES (?, ?, ?, ?, ?, ?)",
                (entity_id, record["id"], entity["type"], entity["label"], float(entity.get("confidence", 0.7)), entity.get("source", "client")),
            )
            conn.execute(
                "INSERT INTO relations (id, record_id, subject, predicate, object, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                (stable_id(record["id"], relation_for(entity["type"]), entity["label"]), record["id"], record["patientCode"], relation_for(entity["type"]), entity["label"], float(entity.get("confidence", 0.7))),
            )

        for file_item in record["files"]:
            name = str(file_item.get("name") or "archivo")
            evidence_id = stable_id(record["id"], name)
            conn.execute(
                "INSERT OR REPLACE INTO evidence (id, record_id, name, mime_type, size, storage_uri, sha256) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evidence_id, record["id"], name, file_item.get("type"), int(file_item.get("size") or 0), file_item.get("storageUri"), file_item.get("sha256")),
            )
            conn.execute(
                "INSERT INTO relations (id, record_id, subject, predicate, object, confidence, evidence_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (stable_id(record["id"], "evidencia_asociada", name), record["id"], record["patientCode"], "evidencia_asociada", name, 0.85, evidence_id),
            )

        conn.execute(
            "INSERT INTO records_fts (record_id, notes, domain, record_type, operator, patient_code) VALUES (?, ?, ?, ?, ?, ?)",
            (record["id"], record["notes"], record["domain"], record["recordType"], record["operator"], record["patientCode"]),
        )
    record["ragChunks"] = index_record_in_rag(record)
    return record


def row_to_record(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    entities = [dict(item) for item in conn.execute("SELECT type, label, confidence, source FROM entities WHERE record_id = ? ORDER BY type, label", (row["id"],))]
    files = [dict(item) for item in conn.execute("SELECT name, mime_type AS type, size, storage_uri AS storageUri, sha256 FROM evidence WHERE record_id = ? ORDER BY name", (row["id"],))]
    return {
        "id": row["id"],
        "createdAt": row["created_at"],
        "date": row["capture_date"],
        "domain": row["domain"],
        "recordType": row["record_type"],
        "patientCode": row["patient_code"],
        "hasPrivateIdentity": bool(row["has_private_identity"]),
        "operator": row["operator"],
        "notes": row["notes"],
        "files": files,
        "entities": entities,
        "graph": build_graph(row["patient_code"], entities, files),
    }


def list_records() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM records ORDER BY created_at DESC LIMIT 250").fetchall()
        return [row_to_record(row, conn) for row in rows]


def records_by_ids(record_ids: list[str]) -> list[dict]:
    if not record_ids:
        return []
    placeholders = ",".join("?" for _ in record_ids)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM records WHERE id IN ({placeholders})", record_ids).fetchall()
        by_id = {row["id"]: row_to_record(row, conn) for row in rows}
    return [by_id[item] for item in record_ids if item in by_id]


def search_records(query: str) -> list[dict]:
    if not query:
        return list_records()
    terms = re.findall(r"[\w*]+", query, flags=re.UNICODE)
    if not terms:
        return []
    fts_query = " OR ".join(f'"{term}"' for term in terms[:8])
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT r.* FROM records_fts f
            JOIN records r ON r.id = f.record_id
            WHERE records_fts MATCH ?
            ORDER BY rank
            LIMIT 50
            """,
            (fts_query,),
        ).fetchall()
        return [row_to_record(row, conn) for row in rows]


class Handler(BaseHTTPRequestHandler):
    server_version = "Evidentia/0.1"

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        relative = "index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/")
        file_path = (ROOT / relative).resolve()
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"ok": True, "database": str(DB_PATH), "records": len(list_records())})
            return
        if parsed.path == "/api/records":
            self.write_json({"records": list_records()})
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self.write_json({"records": search_records(query)})
            return
        if parsed.path == "/api/rag/stats":
            self.write_json(rag_stats())
            return
        if parsed.path == "/api/ai/status":
            self.write_json(ai_status())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/records":
            try:
                payload = self.read_json()
                record = save_record(normalize_record(payload))
                self.write_json({"record": record}, status=201)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/uploads":
            try:
                self.write_json({"files": self.save_uploaded_files()}, status=201)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/chat":
            try:
                payload = self.read_json()
                self.write_json(query_rag(str(payload.get("question") or "")))
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        self.write_json({"error": "not found"}, status=404)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def save_uploaded_files(self) -> list[dict]:
        content_type = self.headers.get("Content-Type", "")
        match = re.search(r"boundary=(.+)", content_type)
        if "multipart/form-data" not in content_type or not match:
            raise ValueError("multipart/form-data required")
        boundary = ("--" + match.group(1).strip().strip('"')).encode("utf-8")
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        saved: list[dict] = []
        for part in raw.split(boundary):
            if b"Content-Disposition" not in part or b"filename=" not in part:
                continue
            header_blob, _, body = part.partition(b"\r\n\r\n")
            disposition = header_blob.decode("utf-8", errors="replace")
            filename_match = re.search(r'filename="([^"]*)"', disposition)
            if not filename_match:
                continue
            original_name = Path(filename_match.group(1)).name or "archivo"
            body = body.rstrip(b"\r\n-")
            digest = hashlib.sha256(body).hexdigest()
            stored_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{digest[:12]}_{safe_filename(original_name)}"
            target = UPLOAD_DIR / stored_name
            target.write_bytes(body)
            saved.append({
                "name": original_name,
                "type": mimetypes.guess_type(original_name)[0] or "application/octet-stream",
                "size": len(body),
                "storageUri": str(target.relative_to(ROOT)),
                "sha256": digest,
            })
        return saved

    def write_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        file_path = (ROOT / relative).resolve()
        if ROOT not in file_path.parents and file_path != ROOT:
            self.send_error(403)
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    connect().close()
    server = ThreadingHTTPServer(("127.0.0.1", 8892), Handler)
    print("Evidentia server running at http://127.0.0.1:8892")
    server.serve_forever()


if __name__ == "__main__":
    main()
