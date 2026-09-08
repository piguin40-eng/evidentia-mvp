#!/usr/bin/env python3
"""
Evidentia local product backbone.

Serves the frontend and persists records, entities, relations, and evidence in
SQLite. It intentionally uses the Python standard library so the first product
loop can run on Miguel's Mac without dependency setup.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import base64
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlrequest
from urllib.parse import parse_qs, quote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("EVIDENTIA_DATA_DIR", str(ROOT / "data"))).expanduser().resolve()
DB_PATH = DATA_DIR / "evidentia.sqlite"
UPLOAD_DIR = DATA_DIR / "uploads"
RAG_DIR = Path(os.getenv("EVIDENTIA_RAG_DIR", str(DATA_DIR / "rag" / "chroma"))).expanduser()
VECTOR_DIR = DATA_DIR / "rag" / "vector"
VECTOR_MATRIX_PATH = VECTOR_DIR / "embeddings.npy"
VECTOR_IDS_PATH = VECTOR_DIR / "chunk_ids.json"
VISION_DIR = DATA_DIR / "vision"
DERIVED_DIR = DATA_DIR / "derived"
AUDIO_DERIVED_DIR = DERIVED_DIR / "audio"
TRANSCRIPT_DIR = DERIVED_DIR / "transcripts"
EXPORT_DIR = DATA_DIR / "exports"
ACCOUNT_REQUESTS_DIR = DATA_DIR / "account-requests"
BACKUP_DIR = DATA_DIR / "backups" / "render-node"
CLIENT_AI_CONFIG_PATH = DATA_DIR / "client_ai_config.json"
BILLING_CONFIG_PATH = DATA_DIR / "billing_config.json"
CHROMA_COLLECTION = "evidentia_knowledge"
ENABLE_CHROMA = os.getenv("EVIDENTIA_ENABLE_CHROMA", "").strip().lower() in {"1", "true", "yes"}
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_CHAT_ENABLED = os.getenv("EVIDENTIA_ENABLE_OPENAI_CHAT", "").strip().lower() in {"1", "true", "yes"}
HOST = os.getenv("EVIDENTIA_HOST", "0.0.0.0")
PORT = int(os.getenv("EVIDENTIA_PORT", "8892"))
BASIC_AUTH_USER = os.getenv("EVIDENTIA_BASIC_AUTH_USER", "").strip()
BASIC_AUTH_PASSWORD = os.getenv("EVIDENTIA_BASIC_AUTH_PASSWORD", "").strip()
BASIC_AUTH_ENABLED = bool(BASIC_AUTH_USER and BASIC_AUTH_PASSWORD)
AUTH_MODE = os.getenv("EVIDENTIA_AUTH_MODE", "basic").strip().lower()
SESSION_COOKIE = "evidentia_session"
SESSION_TOKEN = hashlib.sha256(f"{BASIC_AUTH_USER}:{BASIC_AUTH_PASSWORD}".encode("utf-8")).hexdigest() if BASIC_AUTH_ENABLED else ""
PUBLIC_STATIC_ROOTS = ("assets/", "qa/")
PUBLIC_STATIC_FILES = {
    "app.js",
    "styles.css",
    "sw.js",
    "manifest.webmanifest",
    "icon.svg",
    "reset.html",
    "website.html",
    "website.css",
    "PILOT_LAUNCH_PLAN.md",
}
STREAM_CHUNK_BYTES = int(os.getenv("EVIDENTIA_STREAM_CHUNK_BYTES", str(256 * 1024)))
MAX_CONNECTOR_EXPORT_CHUNKS = int(os.getenv("EVIDENTIA_CONNECTOR_EXPORT_CHUNKS", "2000"))
ALLOWED_CLIENT_AI_PROVIDERS = {"openai", "azure_openai", "anthropic", "local_endpoint"}
ALLOWED_CLIENT_AI_MODES = {"helix_managed", "client_key", "dedicated"}
ALLOWED_BILLING_PLANS = {"personal", "pro", "clinic", "private_node"}
ALLOWED_SUBSCRIPTION_STATES = {"trial", "active", "past_due", "canceled", "manual_pending"}
ALLOWED_PAYMENT_PROVIDERS = {"none", "stripe", "apple_iap", "manual_b2b"}
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_PRICE_ID = os.getenv("STRIPE_EVIDENTIA_PERSONAL_PRICE_ID", "").strip()
PUBLIC_BASE_URL = os.getenv("EVIDENTIA_PUBLIC_BASE_URL", "").strip()
ALLOW_STRIPE_SANDBOX = os.getenv("EVIDENTIA_ALLOW_STRIPE_SANDBOX", "").strip().lower() in {"1", "true", "yes"}


def normalize_auth_user(value: str) -> str:
    return (value or "").strip().casefold()


def normalize_auth_secret(value: str) -> str:
    return re.sub(r"[\s\-_.]+", "", value or "").casefold()


def valid_credentials(username: str, password: str) -> bool:
    if not BASIC_AUTH_ENABLED:
        return True
    expected_user = normalize_auth_user(BASIC_AUTH_USER)
    incoming_user = normalize_auth_user(username)
    if not hmac.compare_digest(incoming_user, expected_user):
        return False

    incoming_secret = normalize_auth_secret(password)
    expected_secret = normalize_auth_secret(BASIC_AUTH_PASSWORD)
    if hmac.compare_digest(incoming_secret, expected_secret):
        return True

    # Convenience for the private local demo: if the configured secret embeds
    # the user name as a prefix, allow typing just the remaining code.
    if expected_secret.startswith(expected_user):
        short_secret = expected_secret[len(expected_user):]
        if short_secret and hmac.compare_digest(incoming_secret, short_secret):
            return True
    return False


ENTITY_RULES = [
    ("discipline", "Ortodoncia", re.compile(r"ortodoncia|alineador|bracket|oclusion|oclusión|maloclusion|maloclusión", re.I)),
    ("discipline", "Rehabilitacion", re.compile(r"rehabilitacion|rehabilitación|protesis|prótesis|implante|implantologia|implantología", re.I)),
    ("discipline", "Estetica dental", re.compile(r"estetica|estética|sonrisa|carilla|veneer|mockup|mocap", re.I)),
    ("discipline", "Periodoncia", re.compile(r"periodoncia|encia|encía|periodontal|gingival", re.I)),
    ("knowledge", "Nota de conocimiento", re.compile(r"nota|transcripcion|transcripción|decision|decisión|criterio|observacion|observación", re.I)),
    ("knowledge", "Protocolo o aprendizaje", re.compile(r"protocolo|aprendizaje|leccion|lección|recordar|conocimiento", re.I)),
    ("measurement", "CIELAB", re.compile(r"cielab|l\*|a\*|b\*|delta e|de00", re.I)),
    ("measurement", "Medicion", re.compile(r"medicion|medición|medida|espesor|grosor|\d+(?:[.,]\d+)?\s*mm", re.I)),
    ("outcome", "Resultado o seguimiento", re.compile(r"resultado|exito|éxito|fracaso|estable|seguimiento|dolor|problema|revision|revisión", re.I)),
    ("pattern", "Patron odontologico", re.compile(r"patron|patrón|recurrencia|repetido|similar|similares|tendencia", re.I)),
    ("clinical_focus", "Seguimiento oclusal", re.compile(r"oclusal|oclusion|oclusión|mordida|contactos|guia anterior|guía anterior|desoclusion|desoclusión", re.I)),
]


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    VISION_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNT_REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
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

        CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts USING fts5(
            chunk_id UNINDEXED,
            record_id UNINDEXED,
            source_name UNINDEXED,
            text
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


def comparable_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


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
    if mime_type.startswith("audio/") or suffix in {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".aac", ".flac"}:
        return transcribe_media(path, media_kind="audio")
    if mime_type.startswith("video/") or suffix in {".mp4", ".mov", ".m4v", ".webm"}:
        return analyze_video(path)
    return "Archivo guardado para el mapa de conocimiento: " + path.name


def transcribe_media(path: Path, media_kind: str = "media") -> str:
    AUDIO_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg"):
        return f"{media_kind.capitalize()} guardado sin transcripcion: ffmpeg no esta disponible. Archivo: {path.name}"
    if not shutil.which("whisper"):
        return f"{media_kind.capitalize()} guardado sin transcripcion: Whisper CLI no esta disponible. Archivo: {path.name}"

    with path.open("rb") as source:
        source_sample = source.read(1024).hex()
    source_key = stable_id(path.name, str(path.stat().st_size), source_sample)
    audio_path = AUDIO_DERIVED_DIR / f"{source_key}_{safe_filename(path.stem)}.wav"
    transcript_json = TRANSCRIPT_DIR / f"{audio_path.stem}.json"
    transcript_txt = TRANSCRIPT_DIR / f"{audio_path.stem}.txt"

    try:
        if not audio_path.exists() or audio_path.stat().st_size == 0:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(audio_path),
                ],
                timeout=180,
                check=True,
            )
        if not transcript_json.exists() or transcript_json.stat().st_size == 0:
            subprocess.run(
                [
                    "whisper",
                    str(audio_path),
                    "--model",
                    "turbo",
                    "--output_format",
                    "json",
                    "--output_dir",
                    str(TRANSCRIPT_DIR),
                ],
                timeout=900,
                check=True,
                text=True,
                capture_output=True,
            )
    except subprocess.TimeoutExpired:
        return f"{media_kind.capitalize()} guardado; transcripcion pendiente porque el procesamiento supero el tiempo limite local. Archivo: {path.name}"
    except Exception as exc:
        return f"{media_kind.capitalize()} guardado; fallo la transcripcion local. Archivo: {path.name}. Error: {exc}"

    try:
        payload = json.loads(transcript_json.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"{media_kind.capitalize()} guardado; Whisper genero una salida no legible. Archivo: {path.name}. Error: {exc}"

    segments = payload.get("segments") or []
    language = payload.get("language") or "desconocido"
    lines = [
        f"Transcripcion local de {media_kind}: {path.name}.",
        f"Idioma detectado: {language}.",
        f"Audio derivado: {audio_path.relative_to(ROOT)}.",
        f"Transcripcion JSON: {transcript_json.relative_to(ROOT)}.",
        "El texto siguiente se indexa en el RAG con marcas de tiempo aproximadas:",
    ]
    plain_lines = []
    for segment in segments:
        start = float(segment.get("start") or 0)
        end = float(segment.get("end") or 0)
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        timestamp = f"[{format_timestamp(start)} - {format_timestamp(end)}]"
        lines.append(f"{timestamp} {text}")
        plain_lines.append(f"{timestamp} {text}")

    if not plain_lines:
        fallback_text = str(payload.get("text") or "").strip()
        if fallback_text:
            lines.append(fallback_text)
            plain_lines.append(fallback_text)
    if plain_lines:
        transcript_txt.write_text("\n".join(plain_lines) + "\n", encoding="utf-8")
        lines.append(f"Transcripcion TXT: {transcript_txt.relative_to(ROOT)}.")
    else:
        lines.append("Whisper no devolvio texto transcribible.")

    lines.append("Advertencia: la transcripcion puede contener errores y debe revisarse antes de usarla como criterio definitivo.")
    return "\n".join(lines)


def format_timestamp(seconds: float) -> str:
    seconds = max(0, seconds)
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


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
    transcript = transcribe_media(path, media_kind="video")
    return (
        f"Analisis visual local de video: {path.name}; duracion {duration}; frames extraidos {len(frame_paths)}. "
        + " ".join(frame_analysis)
        + " "
        + transcript
        + " Vision semantica avanzada pendiente de activar."
    )


def index_record_in_rag(record: dict) -> int:
    collection = None
    if ENABLE_CHROMA:
        try:
            collection = get_chroma_collection()
        except Exception:
            pass
    chunks_payload: list[tuple[str, str, str]] = []
    notes_text = record["notes"]
    normalized_notes = comparable_text(notes_text)
    chunks_payload.append(("nota del caso", "record_notes", notes_text))

    for file_item in record.get("files", []):
        storage_uri = file_item.get("storageUri")
        name = str(file_item.get("name") or "archivo")
        if not storage_uri:
            continue
        path = (ROOT / storage_uri).resolve()
        if ROOT not in path.parents and path != ROOT:
            continue
        if path.exists():
            file_text = extract_text_from_path(path, file_item.get("type"))
            normalized_file = comparable_text(file_text)
            if normalized_file and normalized_file not in normalized_notes and normalized_notes not in normalized_file:
                chunks_payload.append((name, "file_text", file_text))

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
        conn.execute("DELETE FROM rag_chunks_fts WHERE record_id = ?", (record["id"],))
        conn.executemany(
            "INSERT OR REPLACE INTO rag_chunks (id, record_id, source_name, chunk_index, text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.executemany(
            "INSERT INTO rag_chunks_fts (chunk_id, record_id, source_name, text) VALUES (?, ?, ?, ?)",
            [(chunk_id, record_id, source_name, text) for chunk_id, record_id, source_name, _index, text, _created_at in rows],
        )

    if collection is not None:
        try:
            collection.delete(where={"record_id": record["id"]})
        except Exception:
            pass
        if ids:
            collection.add(ids=ids, documents=docs, metadatas=metadatas)
    return len(ids)


def rag_stats() -> dict:
    latest_snapshot = latest_local_snapshot()
    stats = {
        "path": str(RAG_DIR),
        "collection": CHROMA_COLLECTION,
        "chunks": 0,
        "backend": "compact_vector",
        "vectorPath": str(VECTOR_MATRIX_PATH),
        "compactVectorChunks": 0,
        "latestSnapshot": latest_snapshot,
        "externalRestoreVerified": False,
    }
    if VECTOR_IDS_PATH.exists():
        try:
            with VECTOR_IDS_PATH.open("r", encoding="utf-8") as handle:
                stats["compactVectorChunks"] = len(json.load(handle))
            stats["chunks"] = stats["compactVectorChunks"]
        except Exception as exc:
            stats["vectorError"] = str(exc)
    if ENABLE_CHROMA:
        try:
            stats["chromaChunks"] = get_chroma_collection().count()
        except Exception as exc:
            stats["chromaError"] = str(exc)
    with connect() as conn:
        stats["sqliteChunks"] = conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
        stats["records"] = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        stats["yolitoRecords"] = conn.execute("SELECT COUNT(*) FROM records WHERE record_type = ?", ("Yolito Ceram source",)).fetchone()[0]
    return stats


def latest_local_snapshot() -> dict:
    candidates = []
    directories = [BACKUP_DIR, DATA_DIR / "backups" / "local-node"]
    if DATA_DIR == (ROOT / "data").resolve():
        directories.append(ROOT / "backups" / "local-node")
    for directory in directories:
        if not directory.exists():
            continue
        candidates.extend(path for path in directory.glob("*.tar.gz") if path.is_file())

    if not candidates:
        return {
            "exists": False,
            "path": "",
            "createdAt": "",
            "sizeBytes": 0,
        }

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    try:
        display_path = str(latest.relative_to(ROOT))
    except ValueError:
        display_path = str(latest)
    return {
        "exists": True,
        "path": display_path,
        "createdAt": datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "sizeBytes": latest.stat().st_size,
    }


def create_runtime_backup() -> dict:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = BACKUP_DIR / f"evidentia-data-{stamp}.tar.gz"
    retention = int(os.getenv("EVIDENTIA_BACKUP_RETENTION", "14"))

    with tempfile.TemporaryDirectory(prefix="evidentia-runtime-backup.") as staging_name:
        staging = Path(staging_name)
        staged_data = staging / "data"
        staged_data.mkdir(parents=True, exist_ok=True)

        source = sqlite3.connect(DB_PATH)
        target = sqlite3.connect(staged_data / "evidentia.sqlite")
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()

        for item in ("uploads", "rag", "derived", "exports"):
            source_path = DATA_DIR / item
            target_path = staged_data / item
            if source_path.exists():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            else:
                target_path.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive, "w:gz") as tar:
            tar.add(staged_data, arcname="data", recursive=True)

        staged_db = staged_data / "evidentia.sqlite"
        with sqlite3.connect(staged_db) as conn:
            records = conn.execute("select count(*) from records").fetchone()[0]
            chunks = conn.execute("select count(*) from rag_chunks").fetchone()[0]
            evidence = conn.execute("select count(*) from evidence").fetchone()[0]

        chunk_ids_path = staged_data / "rag" / "vector" / "chunk_ids.json"
        compact_vector_ids = 0
        if chunk_ids_path.exists():
            compact_vector_ids = len(json.loads(chunk_ids_path.read_text(encoding="utf-8")))

    archives = sorted(BACKUP_DIR.glob("evidentia-data-*.tar.gz"), key=lambda path: path.stat().st_mtime, reverse=True)
    removed = 0
    for stale in archives[retention:]:
        stale.unlink()
        removed += 1

    return {
        "ok": True,
        "archive": str(archive),
        "sizeBytes": archive.stat().st_size,
        "records": records,
        "sqliteChunks": chunks,
        "evidence": evidence,
        "compactVectorChunkIds": compact_vector_ids,
        "retention": retention,
        "removed": removed,
        "createdAt": stamp,
    }


def rebuild_runtime_vector_index() -> dict:
    script = ROOT / "scripts" / "rebuild_compact_vector_index.py"
    env = os.environ.copy()
    env["EVIDENTIA_DATA_DIR"] = str(DATA_DIR)
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    payload = {
        "ok": completed.returncode == 0,
        "returnCode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    try:
        parsed = json.loads(completed.stdout.strip().splitlines()[-1])
        payload.update(parsed)
    except Exception:
        pass
    return payload


def ai_status() -> dict:
    client_ai = client_ai_status()
    if client_ai.get("active"):
        return {
            "provider": client_ai.get("provider"),
            "active": True,
            "model": client_ai.get("model"),
            "mode": client_ai.get("mode"),
            "tenant": client_ai.get("tenantName"),
            "privacyMode": client_ai.get("privacyMode"),
            "monthlyBudget": client_ai.get("monthlyBudget"),
            "message": "IA del comprador activa; proveedor configurado en servidor",
        }
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return {
        "provider": "openai",
        "active": bool(api_key and OPENAI_CHAT_ENABLED),
        "model": OPENAI_MODEL if api_key and OPENAI_CHAT_ENABLED else None,
        "mode": "openai" if api_key and OPENAI_CHAT_ENABLED else "rag-local",
        "message": "OpenAI activo" if api_key and OPENAI_CHAT_ENABLED else "Chat RAG local activo; sintesis externa desactivada por defecto",
    }


def default_client_ai_config() -> dict:
    return {
        "tenantName": "",
        "mode": "helix_managed",
        "provider": "openai",
        "model": OPENAI_MODEL,
        "endpoint": "",
        "monthlyBudget": "",
        "privacyMode": "local_first",
        "externalAiEnabled": False,
        "apiKey": "",
        "updatedAt": "",
    }


def load_client_ai_config(include_secret: bool = False) -> dict:
    config = default_client_ai_config()
    if CLIENT_AI_CONFIG_PATH.exists():
        try:
            raw = json.loads(CLIENT_AI_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                config.update(raw)
        except Exception:
            pass
    if not include_secret:
        config.pop("apiKey", None)
        config["apiKeyPresent"] = bool(load_client_ai_config(include_secret=True).get("apiKey"))
    return config


def default_billing_config() -> dict:
    return {
        "plan": "personal",
        "priceEurMonthly": "5.99",
        "subscriptionStatus": "trial",
        "paymentProvider": "none",
        "workspaceId": "",
        "accountEmail": "",
        "currentPeriodEnd": "",
        "storageLimitMb": 512,
        "queryLimitMonthly": 250,
        "aiIncluded": False,
        "updatedAt": "",
    }


def load_billing_config() -> dict:
    config = default_billing_config()
    if BILLING_CONFIG_PATH.exists():
        try:
            raw = json.loads(BILLING_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                config.update(raw)
        except Exception:
            pass
    return config


def billing_status() -> dict:
    config = load_billing_config()
    provider_ready = config.get("paymentProvider") in {"stripe", "apple_iap", "manual_b2b"}
    privacy_ready = os.getenv("EVIDENTIA_PRIVACY_TERMS_READY", "").strip().lower() in {"1", "true", "yes"}
    stripe_sandbox_ready = bool(ALLOW_STRIPE_SANDBOX and STRIPE_SECRET_KEY.startswith("sk_test_") and STRIPE_PRICE_ID.startswith("price_") and PUBLIC_BASE_URL.startswith("https://"))
    active = config.get("subscriptionStatus") in {"trial", "active", "manual_pending"}
    return {
        "plan": config.get("plan") or "personal",
        "priceEurMonthly": str(config.get("priceEurMonthly") or "5.99"),
        "subscriptionStatus": config.get("subscriptionStatus") or "trial",
        "paymentProvider": config.get("paymentProvider") or "none",
        "workspaceId": config.get("workspaceId") or "",
        "accountEmail": config.get("accountEmail") or "",
        "currentPeriodEnd": config.get("currentPeriodEnd") or "",
        "storageLimitMb": int(config.get("storageLimitMb") or 512),
        "queryLimitMonthly": int(config.get("queryLimitMonthly") or 250),
        "aiIncluded": bool(config.get("aiIncluded")),
        "providerReady": provider_ready,
        "privacyTermsReady": privacy_ready,
        "stripeSandboxReady": stripe_sandbox_ready,
        "active": active,
        "liveChargingEnabled": False,
        "message": "Billing sandbox/local activo; cobro real desactivado hasta aprobacion explicita",
        "updatedAt": config.get("updatedAt") or "",
    }


def save_billing_config(payload: dict) -> dict:
    current = load_billing_config()
    plan = str(payload.get("plan") or current.get("plan") or "personal").strip()
    status = str(payload.get("subscriptionStatus") or current.get("subscriptionStatus") or "trial").strip()
    provider = str(payload.get("paymentProvider") or current.get("paymentProvider") or "none").strip()
    if plan not in ALLOWED_BILLING_PLANS:
        raise ValueError("plan de suscripcion no permitido")
    if status not in ALLOWED_SUBSCRIPTION_STATES:
        raise ValueError("estado de suscripcion no permitido")
    if provider not in ALLOWED_PAYMENT_PROVIDERS:
        raise ValueError("proveedor de pago no permitido")

    account_email = str(payload.get("accountEmail") or current.get("accountEmail") or "").strip()
    workspace_id = str(payload.get("workspaceId") or current.get("workspaceId") or "").strip()
    if account_email and not workspace_id:
        workspace_id = stable_id("workspace", account_email)

    config = {
        "plan": plan,
        "priceEurMonthly": str(payload.get("priceEurMonthly") or current.get("priceEurMonthly") or "5.99").strip(),
        "subscriptionStatus": status,
        "paymentProvider": provider,
        "workspaceId": workspace_id,
        "accountEmail": account_email,
        "currentPeriodEnd": str(payload.get("currentPeriodEnd") or current.get("currentPeriodEnd") or "").strip(),
        "storageLimitMb": int(payload.get("storageLimitMb") or current.get("storageLimitMb") or 512),
        "queryLimitMonthly": int(payload.get("queryLimitMonthly") or current.get("queryLimitMonthly") or 250),
        "aiIncluded": bool(payload.get("aiIncluded", current.get("aiIncluded", False))),
        "updatedAt": now_iso(),
    }
    BILLING_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BILLING_CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        BILLING_CONFIG_PATH.chmod(0o600)
    except Exception:
        pass
    return billing_status()


def stripe_form_request(path: str, fields: dict[str, str]) -> dict:
    body = "&".join(
        f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
        for key, value in fields.items()
        if value != ""
    ).encode("utf-8")
    req = urlrequest.Request(
        f"https://api.stripe.com/v1/{path.lstrip('/')}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urlrequest.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def create_checkout_session(payload: dict) -> dict:
    status = billing_status()
    email = str(payload.get("email") or status.get("accountEmail") or "").strip()
    if not status.get("stripeSandboxReady"):
        return {
            "ok": False,
            "blocked": True,
            "reason": "stripe_sandbox_not_configured",
            "message": "Stripe sandbox no esta configurado. Requiere sk_test, price_id, URL publica HTTPS y aprobacion explicita.",
            "liveChargingEnabled": False,
        }
    if not email:
        return {"ok": False, "blocked": True, "reason": "email_required", "message": "Falta email de cuenta", "liveChargingEnabled": False}
    success_url = PUBLIC_BASE_URL.rstrip("/") + "/?billing=success#client-ai"
    cancel_url = PUBLIC_BASE_URL.rstrip("/") + "/?billing=cancel#client-ai"
    try:
        session = stripe_form_request(
            "checkout/sessions",
            {
                "mode": "subscription",
                "line_items[0][price]": STRIPE_PRICE_ID,
                "line_items[0][quantity]": "1",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": email,
                "metadata[product]": "evidentia_personal",
                "metadata[price_eur_monthly]": "5.99",
            },
        )
    except Exception as exc:
        return {"ok": False, "blocked": True, "reason": "stripe_error", "message": str(exc), "liveChargingEnabled": False}
    return {
        "ok": True,
        "provider": "stripe",
        "mode": "sandbox",
        "checkoutSessionId": session.get("id"),
        "checkoutUrl": session.get("url"),
        "liveChargingEnabled": False,
    }


def client_ai_status() -> dict:
    config = load_client_ai_config(include_secret=True)
    has_secret = bool(config.get("apiKey")) or config.get("provider") == "local_endpoint"
    active = bool(config.get("externalAiEnabled") and has_secret)
    return {
        "tenantName": config.get("tenantName") or "",
        "mode": config.get("mode") or "helix_managed",
        "provider": config.get("provider") or "openai",
        "model": config.get("model") or OPENAI_MODEL,
        "endpoint": config.get("endpoint") or "",
        "privacyMode": config.get("privacyMode") or "local_first",
        "monthlyBudget": config.get("monthlyBudget") or "",
        "updatedAt": config.get("updatedAt") or "",
        "apiKeyPresent": bool(config.get("apiKey")),
        "active": active,
    }


def save_client_ai_config(payload: dict) -> dict:
    current = load_client_ai_config(include_secret=True)
    mode = str(payload.get("mode") or current.get("mode") or "helix_managed").strip()
    provider = str(payload.get("provider") or current.get("provider") or "openai").strip()
    if mode not in ALLOWED_CLIENT_AI_MODES:
        raise ValueError("modo de IA no permitido")
    if provider not in ALLOWED_CLIENT_AI_PROVIDERS:
        raise ValueError("proveedor de IA no permitido")

    api_key = str(payload.get("apiKey") or "").strip()
    if not api_key and payload.get("keepExistingApiKey", True):
        api_key = str(current.get("apiKey") or "").strip()

    config = {
        "tenantName": str(payload.get("tenantName") or "").strip(),
        "mode": mode,
        "provider": provider,
        "model": str(payload.get("model") or OPENAI_MODEL).strip(),
        "endpoint": str(payload.get("endpoint") or "").strip(),
        "monthlyBudget": str(payload.get("monthlyBudget") or "").strip(),
        "privacyMode": str(payload.get("privacyMode") or "local_first").strip(),
        "externalAiEnabled": bool(payload.get("externalAiEnabled")),
        "apiKey": api_key,
        "updatedAt": now_iso(),
    }
    CLIENT_AI_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLIENT_AI_CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        CLIENT_AI_CONFIG_PATH.chmod(0o600)
    except Exception:
        pass
    return client_ai_status()


def test_client_ai_config() -> dict:
    config = load_client_ai_config(include_secret=True)
    provider = config.get("provider")
    if provider == "local_endpoint":
        return {"ok": bool(config.get("endpoint")), "message": "Endpoint local configurado" if config.get("endpoint") else "Falta endpoint local"}
    if provider != "openai":
        return {"ok": False, "message": "Test automatico v1 disponible solo para OpenAI; guardar proveedor y validar en despliegue dedicado"}
    api_key = str(config.get("apiKey") or "").strip()
    if not api_key:
        return {"ok": False, "message": "Falta API key del comprador"}
    req = urlrequest.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            return {"ok": 200 <= response.status < 300, "message": "Conexion OpenAI validada con la clave del comprador"}
    except Exception as exc:
        return {"ok": False, "message": f"No se pudo validar la conexion: {exc}"}


def demo_status() -> dict:
    rag = rag_stats()
    ai = ai_status()
    records = len(list_records())
    chunks = int(rag.get("chunks") or rag.get("compactVectorChunks") or rag.get("sqliteChunks") or 0)
    commercial_gate = latest_commercial_gate_status()
    value_evidence = latest_founder_value_evidence()
    checks = [
        {"name": "records", "ok": records >= 3, "detail": f"{records} registros"},
        {"name": "rag", "ok": chunks >= 100, "detail": f"{chunks} chunks"},
        {"name": "ai_local", "ok": ai.get("mode") == "rag-local" and not bool(ai.get("active")), "detail": ai.get("mode") or "unknown"},
        {"name": "runtime", "ok": Path.cwd().resolve() == ROOT, "detail": str(Path.cwd().resolve())},
    ]
    decision = "VERDE" if all(check["ok"] for check in checks) else "AMARILLO"
    sellable_readiness = sellable_readiness_gate(decision, rag, commercial_gate)
    return {
        "ok": decision == "VERDE",
        "decision": decision,
        "records": records,
        "chunks": chunks,
        "backend": rag.get("backend"),
        "externalAiActive": bool(ai.get("active")),
        "checks": checks,
        "commercialGate": commercial_gate,
        "sellableReadiness": sellable_readiness,
        "valueEvidence": value_evidence,
        "message": "Demo local-first lista para mostrar" if decision == "VERDE" else "Revisar nodo antes de demo",
    }


def sellable_readiness_gate(demo_decision: str, rag: dict, commercial_gate: dict) -> dict:
    reasons = []
    if demo_decision != "VERDE":
        reasons.append({
            "code": "demo_not_green",
            "label": "Demo tecnica no verificada",
            "detail": "Revalidar runtime, registros, RAG local e IA externa apagada antes de mostrar.",
        })
    if rag.get("externalRestoreVerified") is not True:
        reasons.append({
            "code": "external_restore_unverified",
            "label": "Restore externo pendiente",
            "detail": "No prometer continuidad ni instalacion portable hasta restore externo PASS.",
        })
    if not commercial_gate.get("sellable"):
        reasons.append({
            "code": "commercial_owner_missing",
            "label": "Owner comercial no validado",
            "detail": commercial_gate.get("nextAction") or "Completar owner, relacion, frase, fecha y permiso antes de contactar.",
        })

    ok = not reasons
    return {
        "ok": ok,
        "blocked": not ok,
        "decision": "PILOTO_PEDIBLE" if ok else "DEMO_CONTROLADA",
        "message": "Piloto fundador pedible con alcance y limites." if ok else "Demo controlada; no apto para difusion externa ni piloto portable.",
        "reasons": reasons,
    }


def latest_commercial_gate_status() -> dict:
    gate_dir = ROOT / "qa" / "microdemo-preflight"
    candidates = sorted(gate_dir.glob("microdemo-preflight-*.md"), key=lambda path: path.stat().st_mtime, reverse=True) if gate_dir.exists() else []
    if not candidates:
        return {
            "exists": False,
            "result": "SIN GATE",
            "score": "",
            "sellable": False,
            "contactAllowed": "NO",
            "nextAction": "Ejecutar scripts/microdemo_preflight_gate.sh antes de una demo comercial.",
            "path": "",
            "gaps": [],
        }

    latest = candidates[0]
    text = latest.read_text(encoding="utf-8", errors="replace")

    def match_line(pattern: str, default: str = "") -> str:
        match = re.search(pattern, text, re.MULTILINE)
        return match.group(1).strip() if match else default

    result = match_line(r"^Resultado:\s*(.+)$", "DESCONOCIDO")
    score = match_line(r"^Score microdemo:\s*(.+)$", "")
    gate_value = match_line(r"^Gate vendible completo:\s*(.+)$", "NO")
    contact_allowed = match_line(r"^- Contactar candidato:\s*(.+)$", "NO")
    next_action = match_line(r"^- Siguiente accion unica:\s*(.+)$") or match_line(r"^## Proxima Accion\s*\n\n(.+)$", "")
    gaps = re.findall(r"^\d+\.\s+(.+)$", text, re.MULTILINE)
    try:
        display_path = str(latest.relative_to(ROOT))
    except ValueError:
        display_path = str(latest)

    return {
        "exists": True,
        "result": result,
        "score": score,
        "sellable": gate_value.upper() == "SI",
        "contactAllowed": contact_allowed,
        "nextAction": next_action,
        "path": display_path,
        "href": "/" + display_path,
        "gaps": gaps[:3],
    }


def latest_founder_value_evidence() -> dict:
    receipts_dir = ROOT / "qa" / "founder-value-receipts"

    def latest_report(pattern: str) -> dict:
        candidates = sorted(receipts_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True) if receipts_dir.exists() else []
        if not candidates:
            return {"exists": False, "path": "", "href": "", "createdAt": ""}
        latest = candidates[0]
        try:
            display_path = str(latest.relative_to(ROOT))
        except ValueError:
            display_path = str(latest)
        created_at = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()
        return {
            "exists": True,
            "path": display_path,
            "href": "/" + display_path,
            "createdAt": created_at,
        }

    return {
        "receipt": latest_report("founder-value-receipt-*.md"),
        "dailyAction": latest_report("daily-commercial-action-*.md"),
    }


def local_index_version() -> str:
    parts = []
    for path in (DB_PATH, VECTOR_MATRIX_PATH, VECTOR_IDS_PATH):
        try:
            stat = path.stat()
            parts.append(f"{path.name}:{int(stat.st_mtime)}:{stat.st_size}")
        except OSError:
            parts.append(f"{path.name}:missing")
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"local-index-{digest}"


SENSITIVE_DECISION_RE = re.compile(
    r"\b(diagnost|diagn[oó]stico|prescri|tratamiento|cirug[ií]a|cl[ií]nic|"
    r"medic|legal|recomienda|recomendaci[oó]n|debo|decidir|decisi[oó]n final)\b",
    re.I,
)


def chat_proof(chunks: list[dict], sources: list[dict], question: str = "") -> dict:
    ai = ai_status()
    non_dental_transfer = is_non_dental_transfer_question(question or "")
    source_types = sorted({
        str(chunk.get("metadata", {}).get("source_type") or "unknown")
        for chunk in chunks
    })
    vector_scores = [
        float(chunk["vector_score"])
        for chunk in chunks
        if isinstance(chunk.get("vector_score"), (int, float))
    ]
    best_vector_score = max(vector_scores) if vector_scores else None
    if len(sources) >= 3 and len(chunks) >= 3:
        evidence_level = "alta"
    elif len(sources) >= 1 and len(chunks) >= 1:
        evidence_level = "media"
    else:
        evidence_level = "baja"
    low_evidence = evidence_level == "baja" or (
        best_vector_score is not None and best_vector_score < 0.18 and len(sources) < 2
    )
    sensitive_decision = bool(SENSITIVE_DECISION_RE.search(question or ""))
    abstention_required = low_evidence or sensitive_decision
    if low_evidence:
        abstention_reason = "evidencia_insuficiente"
    elif sensitive_decision:
        abstention_reason = "decision_sensible_requiere_revision_humana"
    else:
        abstention_reason = ""
    return {
        "evidenceLevel": evidence_level,
        "lowEvidence": low_evidence,
        "abstentionRequired": abstention_required,
        "abstentionReason": abstention_reason,
        "abstentionContract": "Si faltan fuentes suficientes, responder como hueco util y pedir mejor evidencia; no diagnosticar ni decidir.",
        "traceContract": "Cada respuesta vendible debe abrir al menos un fragmento exacto con documento, registro, tipo de recuperacion y responsable humano.",
        "questionIntent": "non_dental_transfer" if non_dental_transfer else "domain_memory",
        "questionIntentLabel": "Transferencia no dental" if non_dental_transfer else "Memoria del nodo",
        "pilotGate": (
            "Para piloto fuera de dental, exigir fuentes propias del negocio antes de venderlo como criterio cerrado."
            if non_dental_transfer
            else "Validar fuentes y responsable humano antes de usarlo como decision operativa."
        ),
        "sourcesReturned": len(sources),
        "chunksReturned": len(chunks),
        "retrievalMode": "+".join(source_types) if source_types else "sin_resultados",
        "bestVectorScore": round(best_vector_score, 3) if best_vector_score is not None else None,
        "externalAiActive": bool(ai.get("active")),
        "indexVersion": local_index_version(),
        "humanReviewRequired": True,
        "medicalOrLegalDecision": False,
    }


def openai_synthesize(question: str, chunks: list[dict]) -> str | None:
    client_ai = load_client_ai_config(include_secret=True)
    client_ai_active = bool(
        client_ai.get("externalAiEnabled")
        and client_ai.get("provider") == "openai"
        and client_ai.get("apiKey")
    )
    if client_ai_active:
        api_key = str(client_ai.get("apiKey") or "").strip()
        model = str(client_ai.get("model") or OPENAI_MODEL).strip()
    else:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = OPENAI_MODEL
    if not ((OPENAI_CHAT_ENABLED or client_ai_active) and api_key and chunks):
        return None

    context = "\n\n".join(
        f"FUENTE {index + 1} | {chunk['metadata'].get('patient_code', 'registro')} | {chunk['metadata'].get('source_name', 'fuente')}\n{chunk['text']}"
        for index, chunk in enumerate(chunks[:8])
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el chat interno de Evidentia: un espejo del conocimiento guardado por una persona, equipo, centro u organizacion. "
                    "Si el tema es dental, responde como especialista en conocimiento dental apoyado en esa memoria, pero no adoptes la personalidad ni el nombre de Yolito, CeramicQ u otro agente vertical. "
                    "Usa el contexto recuperado primero como memoria interna; si el contexto no alcanza, explica el hueco y aporta solo orientacion general claramente marcada como no verificada por la memoria. "
                    "Responde como un chat natural: directo, breve y centrado solo en la pregunta. "
                    "No pegues fragmentos largos del RAG ni conviertas la respuesta en una lista de chunks. "
                    "No inventes datos, relaciones ni conclusiones. Si la evidencia es insuficiente, dilo con claridad como hueco util y pide mejor fuente. "
                    "No diagnostiques, prescribas ni tomes decisiones clinicas, legales o finales. "
                    "Menciona las fuentes solo de forma ligera cuando ayude a verificar la respuesta."
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
        print(f"OpenAI synthesis unavailable; using local RAG answer: {exc}")
        return None


CHAT_STOP_WORDS = {
    "sobre", "para", "como", "cuando", "donde", "desde", "hasta", "entre", "tengo", "tienes", "tiene",
    "esta", "este", "esto", "esta", "esas", "esos", "algo", "todo", "todos", "cual", "cuales",
    "que", "quien", "porque", "pregunta", "respuesta", "hacer", "dime", "explica", "buscar",
    "guardado", "conocimiento", "documento", "documentos", "caso", "casos", "fuente", "fuentes",
}

YOLITO_CHAT_TERMS = {
    "yolito", "ceramica", "cerámica", "ceram", "estratificacion", "estratificación",
    "masa", "masas", "dentina", "deep", "opal", "opalescente", "opalescentes",
    "incisal", "cervical", "tercio", "tercios", "mamelon", "mamelones",
    "halo", "translucido", "translúcido", "clear", "neutral", "ti1", "ti2", "ti3",
    "valor", "croma", "sustrato", "tetraciclina", "tetraciclinas", "discromico",
    "discromía", "feldespática", "feldespatica", "carilla", "carillas", "emax",
    "e.max", "ips", "bigcolor", "cielab", "polarizada",
}


def chat_terms(question: str) -> list[str]:
    terms = []
    for term in re.findall(r"[\wÀ-ÿ*.+-]+", question.lower(), flags=re.UNICODE):
        clean = term.strip(".*+-_")
        if len(clean) < 4 or clean in CHAT_STOP_WORDS:
            continue
        terms.append(clean)
    return terms[:12]


def split_relevant_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\s+-\s+|\n+", cleaned)
    sentences = []
    for part in parts:
        sentence = part.strip(" -•\t")
        if len(sentence) < 35:
            continue
        low = sentence.lower()
        if "duplicate_content" in low or '"path":' in low or '"reason":' in low:
            continue
        if "source_path" in low or "copied_to" in low or "sha256" in low:
            continue
        if sentence.endswith("?") or sentence.endswith("¿"):
            continue
        sentence = clean_chat_sentence(sentence)
        if sentence:
            sentences.append(sentence[:520])
    return sentences


def clean_chat_sentence(sentence: str) -> str:
    sentence = re.split(r"\s+[\[{]\s*['\"]?(?:source_path|path|reason|duplicate_of|copied_to|sha256)['\"]?\s*[:=]", sentence, maxsplit=1)[0]
    sentence = re.sub(r"[{}\[\]]", " ", sentence)
    sentence = re.sub(r"\*\*", "", sentence)
    sentence = re.sub(r"\s+", " ", sentence).strip(" -:;,.")
    sentence = re.sub(r"^(?:\d+[.)]?\s*)+", "", sentence).strip()
    sentence = sentence.replace("DEVO", "debo").replace("TINCIONEN", "tinciones").replace("DESPUES", "despues")
    if len(sentence) < 20:
        return ""
    if sentence.count("/") > 8 or sentence.count('"') > 4:
        return ""
    return sentence


def inline_answers_after_questions(text: str) -> list[str]:
    answers = []
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    for match in re.finditer(r"([^?¿]{20,220}\?)\s*([^?]{35,520})", cleaned):
        tail = match.group(2).strip(" -•\t")
        tail = re.split(r"(?=\s+[A-ZÁÉÍÓÚÑ]{3,}\s*:)|(?=\s+CUANDO\s+)|(?=\s+QUE\s+)", tail)[0].strip()
        tail = clean_chat_sentence(tail)
        if tail and "duplicate_content" not in tail.lower():
            answers.append(tail[:420])
    return answers


def extract_inventory_items(text: str, limit: int = 6) -> list[str]:
    items: list[str] = []
    for match in re.finditer(r"\[[^\]]+\]\s+([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\.[a-z0-9]+)", text or "", flags=re.I):
        name = re.sub(r"\s+", " ", match.group(1)).strip()
        path = re.sub(r"\s+", " ", match.group(2)).strip()
        ext = match.group(3).strip()
        if not name:
            continue
        label = f"{name} ({ext})"
        if path and path != name:
            label += f" en {path}"
        if label not in items:
            items.append(label)
        if len(items) >= limit:
            break
    return items


def is_yolito_chat(question: str, chunks: list[dict]) -> bool:
    question_terms = set(chat_terms(question))
    question_low = question.lower()
    if is_non_dental_transfer_question(question):
        return False
    if question_terms & YOLITO_CHAT_TERMS or any(term in question_low for term in YOLITO_CHAT_TERMS):
        return True
    for chunk in chunks[:8]:
        metadata = chunk.get("metadata", {})
        haystack = " ".join(
            str(metadata.get(key) or "")
            for key in ("record_type", "source_name", "domain", "patient_code")
        ).lower()
        if "yolito" in haystack or "ceram" in haystack:
            return True
    return False


def is_non_dental_transfer_question(question: str) -> bool:
    question_low = question.lower()
    non_dental_signals = (
        "no dental", "sin usar un caso dental", "negocio", "operaciones",
        "propuestas", "reuniones", "documentos internos", "whatsapp",
    )
    return any(signal in question_low for signal in non_dental_signals)


def local_non_dental_transfer_answer(question: str, chunks: list[dict]) -> str:
    return (
        "Evidentia es una memoria contextual local-first: convierte propuestas, reuniones, notas y documentos internos "
        "en conocimiento consultable con fuentes visibles. Para un equipo de operaciones, el valor es recuperar por que "
        "se tomo una decision, que aprendizaje se repite y que evidencia falta antes de actuar. Los datos quedan en el "
        "nodo local y la IA externa es opcional; la respuesta debe enlazar solo a fuentes pertinentes del negocio, "
        "no a ejemplos heredados de otro vertical. Si la fuente no cubre contexto, fecha o responsable, el sistema lo "
        "trata como hueco util, no como certeza."
    )


def yolito_source_notes(chunks: list[dict]) -> list[str]:
    notes: list[str] = []
    for chunk in chunks[:8]:
        text = re.sub(r"\s+", " ", chunk.get("text") or "").strip()
        low = text.lower()
        candidates = []
        if "sustrato determina" in low or "sustrato oscuro" in low:
            candidates.append("El sustrato manda: si hay discromía fuerte, la elección del material debe bloquear antes de buscar estética.")
        if "dixplaxias" in low or "displasias" in low or "tetracicl" in low:
            candidates.append("En tinciones intensas o displasias, no conviene prometer feldespática directa sin estrategia de bloqueo.")
        if "deep dentina" in low or "deep dentin" in low:
            candidates.append("En cervical, usar Deep Dentin del color elegido con control de croma; Orange/Pink solo si ayuda a suavizar transición gingival.")
        if "opalescentes opal1" in low or "opal1" in low:
            candidates.append("En incisal, trabajar opalescentes Opal 1-4, Blue/Violet y mamelones solo si el caso pide halo/profundidad.")
        if "clear" in low and ("ti1" in low or "neutral" in low):
            candidates.append("El cierre de esmalte puede ir con Clear, TI1/TI2/TI3 o Neutral; si el borde ya está gris, cuidado con pasarte de translúcidos neutros.")
        if "bigcolor cera" in low or "polarizada" in low:
            candidates.append("Sin foto polarizada y BigColor Cera gris, CIELAB/Delta E deben tratarse como estimados, no medición clínica absoluta.")
        for candidate in candidates:
            if candidate not in notes:
                notes.append(candidate)
            if len(notes) >= 4:
                return notes
    return notes


def local_yolito_synthesize(question: str, chunks: list[dict]) -> str:
    question_low = question.lower()
    notes = yolito_source_notes(chunks)
    wants_knowledge = bool(re.search(
        r"\b(que es|qué es|cual es|cuál es|define|definicion|definición|explica|"
        r"diferencia|por que|por qué|para que sirve|para qué sirve|como funciona|cómo funciona)\b",
        question_low,
    ))
    wants_recipe = (not wants_knowledge) and any(term in question_low for term in (
        "receta", "formul", "porcentaje", "porcentajes", "estrat", "tercio",
        "tercios", "cervical", "medio", "incisal", "a1", "a2", "b1", "b2",
        "hazme", "dame", "planteame", "plantéame",
    ))
    wants_material = any(term in question_low for term in (
        "material", "sustrato", "tetracicl", "tincion", "tinción", "discrom",
        "bloquear", "feldes", "zircon", "emax",
    ))
    wants_glaze = any(term in question_low for term in (
        "glaseado", "glasear", "glaze", "pasta glaze", "glasé", "glase",
    ))

    if wants_knowledge:
        answer = [
            "Evidentia: respondo desde tu conocimiento guardado; no necesito fotos para explicar conceptos generales.",
        ]
        if any(term in question_low for term in ("feldes", "feldespática", "feldespatica")):
            answer.extend([
                "",
                "La cerámica feldespática es una cerámica vítrea de estratificación muy estética: permite controlar profundidad, textura, fluorescencia, opalescencia y microcapas con mucha finura. Su punto fuerte es la naturalidad óptica; su punto débil es que depende mucho del soporte, espesor, adhesión y sustrato.",
                "",
                "En práctica, no se elige solo por belleza: si el sustrato está favorable y hay espacio, puede ser brillante. Si el fondo es oscuro o muy discromico, una feldespática fina y translúcida puede perder valor o contaminarse; ahí entra el criterio de bloqueo/material antes que el maquillaje.",
            ])
        if any(term in question_low for term in ("disilicato", "ls2", "e.max", "emax")):
            answer.extend([
                "",
                "El disilicato de litio es una cerámica vítrea reforzada. Suele dar más resistencia que una feldespática pura y permite trabajar monolítico, cut-back o estratificado. La elección HT/LT/MO/HO no es estética decorativa: define cuánto deja pasar el fondo y cuánto bloquea.",
            ])
        if any(term in question_low for term in ("zircon", "zirconia", "zirconio", "3y", "4y", "5y")):
            answer.extend([
                "",
                "La zirconia es policristalina, más resistente y menos vítrea. 3Y suele priorizar resistencia/opacidad; 4Y y 5Y suben translucidez a costa de resistencia relativa. En estética anterior no basta decir zirconia: hay que saber generación, espesor, fondo, maquillaje y si llevará recubrimiento.",
            ])
        wants_mass_topic = bool(re.search(r"\b(masa|masas|dentin|dentina|deep|opal|incisal)\b", question_low))
        if wants_mass_topic:
            answer.extend([
                "",
                "Una masa cerámica es una cerámica de estratificación con una funcion optica concreta, no solo un color. Puede aportar cuerpo y valor, como una dentina; subir croma y profundidad, como una Deep Dentin; modular translucidez y opalescencia, como opalescentes o incisales; o crear efectos de halo, mamelón, azul, violeta o neutralidad.",
            ])
        if any(term in question_low for term in ("valor", "croma", "transluc", "opalesc", "fluoresc", "opacidad")):
            answer.extend([
                "",
                "Valor, croma, opacidad, translucidez, fluorescencia y opalescencia son variables ópticas distintas. El valor manda la luminosidad; el croma la saturación; la opacidad bloquea fondo; la translucidez deja pasar luz; la opalescencia enfría o da profundidad según ángulo/luz; la fluorescencia ayuda a que el diente no muera bajo luz UV o luz clínica.",
            ])
        if len(answer) == 1:
            answer.extend([
                "",
                "Puedo explicar masas, familias cerámicas, fondos, espesores, superficie preglaze/glaze, L*a*b*, valor, croma, opacidad, translucidez, fluorescencia, opalescencia, cocción y criterios de selección de material.",
            ])
        answer.extend([
            "",
            "El atlas sirve para responder comportamiento técnico de masas, familias, fondos, superficies, L*a*b*, espesores y tendencias ópticas. Las fotos solo son obligatorias cuando pides receta clínica cerrada, comparación objetivo-restauración, Delta E o porcentajes por tercios aplicados a un caso real.",
        ])
        if notes:
            answer.append("")
            answer.append("Memoria usada: " + " ".join(notes[:2]))
        return "\n".join(answer)

    if wants_recipe:
        answer = [
            "Evidentia: respondo desde tu conocimiento guardado, con criterio y fuentes recuperables.",
            "",
            "Para un caso tipo A2 con incisal gris y bajo valor, el problema principal suele ser valor/opalescencia, no añadir más gris. Yo evitaría cargar el borde con translúcidos neutros desde el principio.",
            "",
            "Cervical: base con dentina/deep dentin del color elegido, controlando croma. Si el cuello se ve pesado, baja saturación y suaviza transición; Orange/Pink solo tendría sentido si hay que unir mejor con tejido gingival.",
            "",
            "Medio: cuerpo luminoso con dentina del tono objetivo y transición fina hacia incisal. Aquí no buscaría efectos fuertes; buscaría estabilidad de valor.",
            "",
            "Incisal: primero subiría valor con opalescentes más claros; después modularía halo/profundidad con Blue/Violet o mamelones en dosis bajas. Clear, TI1/TI2/TI3 o Neutral solo como cierre, con cuidado si el borde ya cae a gris.",
            "",
            "Sin foto polarizada, guía y BigColor Cera gris, esto es orientación de estratificación, no receta clínica cerrada con porcentajes absolutos.",
        ]
        if notes:
            answer.append("")
            answer.append("Memoria usada: " + " ".join(notes[:2]))
        return "\n".join(answer)

    if wants_material:
        answer = [
            "Evidentia: según tu conocimiento guardado, primero hay que leer el contexto antes de recomendar.",
            "",
            "Si el diente está claro o semiclaro y favorable, puedes plantear feldespática sobre platino/refractario o una opción tipo disilicato translúcido según resistencia y espesor. Si hay tinción mínima, el LT puede ayudar a bloquear un poco.",
            "",
            "Si hay tetraciclinas, discromía fuerte o sustrato muy negativo, no vendería una solución fina y translúcida como si fuera segura. Necesitas bloqueo: MO para tinciones moderadas, HO para muy oscuras, o incluso zirconio si el caso lo exige; después estratificación cerámica para recuperar vida.",
            "",
            "Regla dura: si un central está discromico y los demás son positivos, ese diente problemático condiciona el material del conjunto para no acabar con valores incompatibles.",
        ]
        if notes:
            answer.append("")
            answer.append("Memoria usada: " + " ".join(notes[:2]))
        return "\n".join(answer)

    if wants_glaze:
        answer = [
            "Evidentia: según tu conocimiento guardado, el glaseado en carillas no se decide como producto único; se decide por superficie, valor final y riesgo de saturación.",
            "",
            "Criterio práctico: si la carilla ya tiene buen valor y textura, conviene un glaze fino o pulido/glaseado muy controlado para no matar la microtextura. Si el resultado está mate o seco, el glaze ayuda a devolver brillo y profundidad, pero en exceso puede redondear textura y subir sensación artificial.",
            "",
            "Si el problema es óptico, no lo arreglaría solo con glaze: primero separaría si falta valor, croma, translucidez u opalescencia. El glaze es cierre superficial; no debe tapar una estratificación mal resuelta.",
            "",
            "Si faltan fotos polarizadas, guía o BigColor Cera gris, lo marco como orientación desde memoria, no como receta clínica cerrada.",
        ]
        if notes:
            answer.append("")
            answer.append("Memoria usada: " + " ".join(notes[:2]))
        return "\n".join(answer)

    if notes:
        return (
            "Evidentia: con lo que tienes en memoria, el criterio sería este: "
            + " ".join(notes[:3])
            + "\n\nPuedo responder conocimiento cerámico general con el atlas/RAG. Solo pediré fotos cuando la pregunta sea una receta o medición clínica aplicada a un caso."
        )
    return (
        "Evidentia: puedo responder desde tu conocimiento guardado sobre casos, protocolos, materiales, decisiones, fotos, resultados y criterios. "
        "Si faltan fuentes suficientes, lo marcaré como hueco útil en vez de inventar."
    )


def local_chat_synthesize(question: str, chunks: list[dict]) -> str:
    terms = chat_terms(question)
    inventory_items: list[str] = []
    ranked: list[tuple[int, int, str]] = []

    if is_non_dental_transfer_question(question):
        return local_non_dental_transfer_answer(question, chunks)

    if is_yolito_chat(question, chunks):
        return local_yolito_synthesize(question, chunks)

    for chunk_index, chunk in enumerate(chunks[:8]):
        text = chunk.get("text") or ""
        for item in extract_inventory_items(text, limit=4):
            if item not in inventory_items:
                inventory_items.append(item)
        for answer in inline_answers_after_questions(text):
            low = answer.lower()
            score = sum(4 for term in terms if term in low)
            if score or any(term in (text or "").lower() for term in terms):
                priority_boost = max(0, 10 - chunk_index)
                ranked.append((score + 3 + priority_boost, chunk_index, answer))
        for sentence in split_relevant_sentences(text):
            low = sentence.lower()
            score = sum(3 for term in terms if term in low)
            if any(marker in low for marker in ("indica", "recomienda", "utilizar", "seleccion", "selección", "protocolo", "material")):
                score += 1
            if score:
                score += max(0, 5 - chunk_index)
                ranked.append((score, chunk_index, sentence))

    ranked.sort(key=lambda item: (-item[0], item[1], len(item[2])))
    selected: list[str] = []
    seen = set()
    for _, _, sentence in ranked:
        key = sentence[:140].lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(sentence)
        if len(selected) >= 3:
            break

    if inventory_items and ("document" in question.lower() or "archivo" in question.lower()):
        intro = "Tengo localizadas estas fuentes relacionadas:"
        return intro + "\n" + "\n".join(f"- {item}" for item in inventory_items[:6])

    if selected:
        answer = "Según lo que tienes guardado: " + selected[0]
        if len(selected[0]) < 120 and len(selected) > 1:
            answer += "\n\nAdemás, " + selected[1][:320]
        return answer

    source_names = []
    for chunk in chunks[:4]:
        source = chunk.get("metadata", {}).get("source_name") or "fuente guardada"
        if source not in source_names:
            source_names.append(source)
    if source_names:
        return (
            "He encontrado fuentes relacionadas, pero no una respuesta cerrada a esa pregunta. "
            "Las más cercanas son: " + ", ".join(source_names) + "."
        )
    return "No tengo suficiente evidencia guardada para responder eso con rigor."


def sellable_local_answer_guardrails(question: str, answer: str, chunks: list[dict]) -> str:
    question_low = question.lower()
    additions: list[str] = []
    source_names: list[str] = []
    for chunk in chunks[:4]:
        source = chunk.get("metadata", {}).get("source_name") or "fuente local"
        if source not in source_names:
            source_names.append(source)

    if any(term in question_low for term in ("conocimiento conecta", "aprendizaje", "criterio")):
        additions.append("Criterio de memoria local: usar la fuente recuperada para separar aprendizaje reutilizable de opinion suelta.")
    if any(term in question_low for term in ("fuente", "fuentes", "apoyan", "concretas")):
        additions.append("Fuente visible: " + ", ".join(source_names[:3]) + ".")
    if any(term in question_low for term in ("limite", "limites", "decision final", "recomendacion", "recomendación", "parcial")):
        additions.append("Limite: esto no diagnostica ni decide; la decision humana debe confirmar la evidencia antes de actuar.")
    if any(term in question_low for term in ("negocio no dental", "propuestas", "reuniones", "notas", "whatsapp")):
        additions.append("Memoria local: el mismo mirror puede ordenar documentos, reuniones y notas con fuentes, sin enviar datos a una IA externa por defecto.")
    if any(term in question_low for term in ("faltaria", "faltaría", "confiar mas", "confiar más", "fuente recuperada es parcial")):
        additions.append("Falta evidencia cuando la fuente no cubre fecha, contexto, autor o criterio de validacion; en ese caso se pide mejor fuente.")

    if not additions:
        return answer
    existing = answer.lower()
    filtered = [line for line in additions if line.lower() not in existing]
    if not filtered:
        return answer
    return answer.rstrip() + "\n\n" + "\n".join(filtered)


_VECTOR_CACHE: dict[str, object] = {}


def compact_vector_rag_chunks(question: str, limit: int = 6) -> list[dict]:
    if not VECTOR_MATRIX_PATH.exists() or not VECTOR_IDS_PATH.exists():
        return []
    try:
        import numpy as np
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    except Exception:
        return []

    try:
        cache_key = str(VECTOR_MATRIX_PATH)
        if _VECTOR_CACHE.get("key") != cache_key:
            matrix = np.load(VECTOR_MATRIX_PATH, mmap_mode="r")
            with VECTOR_IDS_PATH.open("r", encoding="utf-8") as handle:
                ids = json.load(handle)
            _VECTOR_CACHE.clear()
            _VECTOR_CACHE.update({"key": cache_key, "matrix": matrix, "ids": ids, "embedder": DefaultEmbeddingFunction()})
        matrix = _VECTOR_CACHE["matrix"]
        ids = _VECTOR_CACHE["ids"]
        embedder = _VECTOR_CACHE["embedder"]
        query = np.asarray(embedder([question])[0], dtype="float32")
        norm = np.linalg.norm(query)
        if not norm:
            return []
        query = query / norm
        scores = np.asarray(matrix @ query)
        if scores.size == 0:
            return []
        top_count = min(limit, scores.size)
        top_indexes = np.argpartition(-scores, top_count - 1)[:top_count]
        top_indexes = top_indexes[np.argsort(-scores[top_indexes])]
        chunk_ids = [ids[int(index)] for index in top_indexes]
        score_by_id = {ids[int(index)]: float(scores[int(index)]) for index in top_indexes}
    except Exception:
        return []

    placeholders = ",".join("?" for _ in chunk_ids)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT c.id, c.record_id, c.source_name, c.chunk_index, c.text,
                   c.created_at, r.patient_code, r.domain, r.record_type,
                   r.created_at AS record_created_at
            FROM rag_chunks c
            LEFT JOIN records r ON r.id = c.record_id
            WHERE c.id IN ({placeholders})
            """,
            chunk_ids,
        ).fetchall()
    by_id = {row["id"]: row for row in rows}
    chunks = []
    for chunk_id in chunk_ids:
        row = by_id.get(chunk_id)
        if not row:
            continue
        chunks.append({
            "id": row["id"],
            "text": row["text"],
            "metadata": {
                "record_id": row["record_id"],
                "patient_code": row["patient_code"],
                "domain": row["domain"],
                "record_type": row["record_type"],
                "source_name": row["source_name"],
                "source_type": "compact_vector",
                "chunk_index": row["chunk_index"],
                "chunk_created_at": row["created_at"],
                "record_created_at": row["record_created_at"],
            },
            "distance": 1.0 - score_by_id.get(chunk_id, 0.0),
            "vector_score": score_by_id.get(chunk_id, 0.0),
        })
    return chunks


def query_rag(question: str, n_results: int = 6) -> dict:
    question = question.strip()
    if not question:
        return {"answer": "Haz una pregunta sobre el conocimiento guardado.", "sources": [], "chunks": [], "proof": chat_proof([], [], question)}
    lexical_chunks = lexical_rag_chunks(question, limit=n_results)
    chunks = list(lexical_chunks)
    seen_chunk_ids = {chunk["id"] for chunk in chunks}
    record_ids = []
    vector_error = None
    for chunk in compact_vector_rag_chunks(question, limit=n_results):
        if chunk["id"] in seen_chunk_ids:
            continue
        chunks.append(chunk)
        seen_chunk_ids.add(chunk["id"])
    try:
        if not ENABLE_CHROMA:
            raise RuntimeError("Chroma disabled; compact vector retrieval used.")
        collection = get_chroma_collection()
        result = collection.query(query_texts=[question], n_results=n_results)
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0] if result.get("distances") else [None] * len(ids)
        for chunk_id, doc, metadata, distance in zip(ids, docs, metadatas, distances):
            if chunk_id in seen_chunk_ids:
                continue
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
            seen_chunk_ids.add(chunk_id)
    except Exception as exc:
        vector_error = str(exc)
    for chunk in chunks:
        record_id = chunk.get("metadata", {}).get("record_id")
        if record_id and record_id not in record_ids:
            record_ids.append(record_id)

    sources = records_by_ids(record_ids)
    if not chunks:
        return {
            "answer": (
                "No tengo contenido tuyo guardado suficiente para responder desde tu memoria. "
                "Puedo tratarlo como hueco útil y, si activas IA externa/búsqueda, ampliarlo con conocimiento general separado de tus fuentes."
            ),
            "sources": [],
            "chunks": [],
            "proof": chat_proof([], [], question),
        }

    proof = chat_proof(chunks, sources, question)
    local_answer = sellable_local_answer_guardrails(question, local_chat_synthesize(question, chunks), chunks)
    synthesized = openai_synthesize(question, chunks)
    if synthesized:
        answer = synthesized
    else:
        answer = local_answer
    if proof.get("lowEvidence") and not answer.lower().startswith("no tengo evidencia suficiente"):
        answer = (
            "No tengo evidencia suficiente en tus fuentes para responder eso como criterio cerrado. "
            "Limite operativo: falta confirmar si las fuentes recuperadas cubren contexto, fecha y responsable. "
            "Lo trataria como hueco util: revisa esas fuentes y carga mejor evidencia antes de tomar una decision humana."
        )
    elif proof.get("abstentionRequired") and "revision humana" not in answer.lower() and "revisión humana" not in answer.lower():
        answer = (
            answer
            + "\n\nLímite Evidentia: esto sale de memoria y recuperación local; si afecta a una decisión clínica o final, requiere revisión humana y fuentes completas."
        )
    response = {"answer": answer, "sources": sources, "chunks": chunks, "ai": ai_status(), "proof": proof}
    if vector_error and not any(chunk.get("metadata", {}).get("source_type") == "compact_vector" for chunk in chunks):
        response["rag_warning"] = "Vector search unavailable; SQLite lexical retrieval used."
        response["rag_error"] = vector_error
    return response


def anonymize(raw: str) -> str:
    if not raw:
        return "KNOWLEDGE-BASE"
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
    files = payload.get("files") or []
    if not notes and not files:
        raise ValueError("notes or files are required")
    if not notes and files:
        file_names = ", ".join(str(item.get("name") or "archivo") for item in files[:6])
        notes = "Registro creado desde archivos adjuntos. Fuentes asociadas: " + file_names

    patient_code = str(payload.get("patientCode") or "").strip()
    patient_raw = str(payload.get("patient") or "").strip()
    if not patient_code:
        patient_code = anonymize(patient_raw)

    record_id = str(payload.get("id") or stable_id(patient_code, notes, now_iso()))
    entities = payload.get("entities") or extract_entities(notes)
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
        if entity.get("type") in {"asset", "evidence"}:
            continue
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
    raw_entities = [dict(item) for item in conn.execute("SELECT type, label, confidence, source FROM entities WHERE record_id = ? ORDER BY type, label", (row["id"],))]
    entities = [entity for entity in raw_entities if entity.get("type") not in {"asset", "evidence"}]
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
        rows = conn.execute("SELECT * FROM records ORDER BY created_at DESC LIMIT 1000").fetchall()
        return [row_to_record(row, conn) for row in rows]


def records_by_ids(record_ids: list[str]) -> list[dict]:
    if not record_ids:
        return []
    placeholders = ",".join("?" for _ in record_ids)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM records WHERE id IN ({placeholders})", record_ids).fetchall()
        by_id = {row["id"]: row_to_record(row, conn) for row in rows}
    return [by_id[item] for item in record_ids if item in by_id]


def lexical_rag_chunks(question: str, limit: int = 6) -> list[dict]:
    terms = [term.lower() for term in re.findall(r"[\wÀ-ÿ.*+-]+", question, flags=re.UNICODE) if len(term) >= 4]
    if not terms:
        return []
    fts_query = " OR ".join(f'"{term.replace(chr(34), chr(34) + chr(34))}"' for term in terms[:12])
    if fts_query:
        try:
            with connect() as conn:
                rows = conn.execute(
                    """
                    SELECT c.id, c.record_id, c.source_name, c.chunk_index, c.text,
                           c.created_at, r.patient_code, r.domain, r.record_type,
                           r.created_at AS record_created_at,
                           bm25(rag_chunks_fts) AS rank
                    FROM rag_chunks_fts
                    JOIN rag_chunks c ON c.id = rag_chunks_fts.chunk_id
                    LEFT JOIN records r ON r.id = c.record_id
                    WHERE rag_chunks_fts MATCH ?
                    ORDER BY rank ASC, c.chunk_index ASC
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            if rows:
                return [{
                    "id": row["id"],
                    "text": row["text"],
                    "metadata": {
                        "record_id": row["record_id"],
                        "patient_code": row["patient_code"],
                        "domain": row["domain"],
                        "record_type": row["record_type"],
                        "source_name": row["source_name"],
                        "source_type": "sqlite_fts",
                        "chunk_index": row["chunk_index"],
                        "chunk_created_at": row["created_at"],
                        "record_created_at": row["record_created_at"],
                    },
                    "distance": None,
                    "lexical_score": float(row["rank"]),
                } for row in rows]
        except Exception:
            pass
    matches: list[tuple[int, dict]] = []
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.record_id, c.source_name, c.chunk_index, c.text,
                   c.created_at, r.patient_code, r.domain, r.record_type,
                   r.created_at AS record_created_at
            FROM rag_chunks c
            LEFT JOIN records r ON r.id = c.record_id
            ORDER BY c.created_at DESC, c.chunk_index ASC
            """
        ).fetchall()
    for row in rows:
        text = row["text"] or ""
        haystack = text.lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            matches.append((score, dict(row)))
    matches.sort(key=lambda item: (-item[0], item[1]["chunk_index"]))
    chunks = []
    for score, row in matches[:limit]:
        chunks.append({
            "id": row["id"],
            "text": row["text"],
            "metadata": {
                "record_id": row["record_id"],
                "patient_code": row.get("patient_code") if hasattr(row, "get") else row["patient_code"],
                "domain": row.get("domain") if hasattr(row, "get") else row["domain"],
                "record_type": row.get("record_type") if hasattr(row, "get") else row["record_type"],
                "source_name": row["source_name"],
                "source_type": "sqlite_lexical",
                "chunk_index": row["chunk_index"],
                "chunk_created_at": row.get("created_at") if hasattr(row, "get") else row["created_at"],
                "record_created_at": row.get("record_created_at") if hasattr(row, "get") else row["record_created_at"],
            },
            "distance": None,
            "lexical_score": score,
        })
    return chunks


def list_rag_chunks(limit: int = 1000) -> list[dict]:
    limit = max(1, min(int(limit), MAX_CONNECTOR_EXPORT_CHUNKS))
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, record_id, source_name, chunk_index, text, created_at
            FROM rag_chunks
            ORDER BY created_at DESC, chunk_index ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def build_connector_export() -> dict:
    records = list_records()
    chunks = list_rag_chunks()
    files_count = sum(len(record.get("files") or []) for record in records)
    return {
        "schema": "evidentia.knowledge_bundle.v1",
        "generatedAt": now_iso(),
        "source": "evidentia-local-node",
        "policy": {
            "allowedUse": "Conectar conocimiento validado a agentes, proyectos o automatizaciones bajo permiso del propietario.",
            "humanReviewRequired": True,
            "medicalOrLegalDecision": False,
            "externalTransferRequiresConsent": True,
        },
        "stats": {
            "records": len(records),
            "files": files_count,
            "chunks": len(chunks),
            "database": str(DB_PATH),
            "ragPath": str(RAG_DIR),
            "indexVersion": local_index_version(),
        },
        "records": records,
        "chunks": chunks,
        "connectorHints": [
            {
                "target": "agent_or_project",
                "method": "import_json",
                "recommendedPrompt": "Usa este bundle como memoria privada trazable. Responde citando record_id, source_name y chunk_index. No tomes decisiones clinicas, legales o economicas sin revision humana.",
            },
            {
                "target": "automation",
                "method": "GET /api/connectors/export",
                "recommendedGuardrail": "Limitar acceso a red local, registrar responsable y exigir consentimiento antes de enviar datos fuera del nodo.",
            },
        ],
    }


def build_account_export() -> dict:
    return {
        "exportedAt": now_iso(),
        "billing": billing_status(),
        "clientAi": client_ai_status(),
        "ragStats": rag_stats(),
        "knowledge": build_connector_export(),
        "policy": {
            "scope": "account_data_export",
            "humanReviewRequired": True,
            "deletionIsManual": True,
            "message": "Export trazable del workspace. La eliminacion real requiere revision humana y backup previo.",
        },
    }


def create_delete_request(payload: dict) -> dict:
    email = str(payload.get("email") or load_billing_config().get("accountEmail") or "").strip()
    reason = str(payload.get("reason") or "").strip()
    confirm = str(payload.get("confirm") or "").strip()
    if confirm != "SOLICITO BORRADO":
        raise ValueError("confirm debe ser SOLICITO BORRADO")
    request_id = stable_id("delete-request", email, reason, now_iso())
    body = {
        "ok": True,
        "requestId": request_id,
        "createdAt": now_iso(),
        "email": email,
        "reason": reason,
        "status": "pending_human_review",
        "destructiveActionTaken": False,
        "message": "Solicitud registrada. No se ha borrado ningun dato automaticamente.",
    }
    ACCOUNT_REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    target = ACCOUNT_REQUESTS_DIR / f"delete-request-{request_id}.json"
    target.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        target.chmod(0o600)
    except Exception:
        pass
    body["path"] = str(target.relative_to(ROOT))
    return body


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

    def is_public_static_path(self, path: str) -> bool:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        return relative in PUBLIC_STATIC_FILES or relative.startswith(PUBLIC_STATIC_ROOTS)

    def require_auth(self) -> bool:
        if not BASIC_AUTH_ENABLED:
            return True
        if AUTH_MODE == "cookie":
            cookie_header = self.headers.get("Cookie", "")
            cookies = dict(
                item.strip().split("=", 1)
                for item in cookie_header.split(";")
                if "=" in item
            )
            if hmac.compare_digest(cookies.get(SESSION_COOKIE, ""), SESSION_TOKEN):
                return True
            self.redirect_to_login()
            return False
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            self.send_auth_required()
            return False
        try:
            decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
        except Exception:
            self.send_auth_required()
            return False
        username, sep, password = decoded.partition(":")
        if not sep:
            self.send_auth_required()
            return False
        if valid_credentials(username, password):
            return True
        self.send_auth_required()
        return False

    def require_active_subscription(self) -> bool:
        status = billing_status()
        if status.get("active"):
            return True
        self.write_json(
            {
                "ok": False,
                "blocked": True,
                "reason": "subscription_inactive",
                "subscriptionStatus": status.get("subscriptionStatus") or "unknown",
                "paymentProvider": status.get("paymentProvider") or "none",
                "liveChargingEnabled": False,
                "message": "Suscripcion no activa. Se mantienen disponibles billing, exportacion y solicitud de borrado.",
            },
            status=402,
        )
        return False

    def send_auth_required(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Evidentia"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = b'{"error":"authentication_required"}'
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect_to_login(self) -> None:
        self.send_response(302)
        self.send_header("Location", "/login.html")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def serve_login(self, error: str = "") -> None:
        escaped_error = "<p class='error'>Usuario o clave incorrectos.</p>" if error else ""
        body = f'''<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Evidentia - acceso</title>
    <meta name="theme-color" content="#070809" />
    <style>
      :root {{ color-scheme: dark; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
      body {{ min-height: 100vh; margin: 0; display: grid; place-items: center; background: #070809; color: #f4fbf8; padding: 24px; }}
      main {{ width: min(420px, 100%); }}
      .brand {{ font-size: 30px; font-weight: 800; letter-spacing: .08em; margin-bottom: 10px; }}
      p {{ color: #9fb4ad; line-height: 1.45; }}
      form {{ display: grid; gap: 14px; margin-top: 26px; }}
      label {{ display: grid; gap: 7px; color: #d7e7e2; font-size: 13px; }}
      input {{ appearance: none; border: 1px solid #28423d; background: #0d1413; color: white; border-radius: 12px; padding: 14px; font-size: 16px; }}
      button {{ border: 0; border-radius: 12px; padding: 15px; font-weight: 800; background: #9ff4dc; color: #06110e; font-size: 16px; }}
      .error {{ color: #ffb4a8; }}
    </style>
  </head>
  <body>
    <main>
      <div class="brand">EVIDENTIA</div>
      <p>Acceso privado al nodo de conocimiento. Inicia sesion para continuar.</p>
      {escaped_error}
      <form method="post" action="/api/login">
        <label>Usuario<input name="username" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" required /></label>
        <label>Clave<input name="password" type="password" autocomplete="current-password" required /></label>
        <button type="submit">Entrar</button>
      </form>
    </main>
  </body>
</html>'''
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_login(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            payload = json.loads(raw or "{}")
            username = str(payload.get("username") or "")
            password = str(payload.get("password") or "")
        else:
            payload = parse_qs(raw)
            username = payload.get("username", [""])[0]
            password = payload.get("password", [""])[0]
        if valid_credentials(username, password):
            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={SESSION_TOKEN}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.serve_login(error="1")

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/login.html":
            self.send_response(200)
            self.end_headers()
            return
        if not self.is_public_static_path(parsed.path) and not self.require_auth():
            return
        relative = "index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/")
        file_path = (ROOT / relative).resolve()
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_cache_headers(file_path)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/healthz":
            self.write_json({"ok": True, "service": "evidentia"})
            return
        if parsed.path == "/login.html":
            self.serve_login()
            return
        if self.is_public_static_path(parsed.path):
            self.serve_static(parsed.path)
            return
        if not self.require_auth():
            return
        if parsed.path == "/api/health":
            self.write_json({"ok": True, "database": str(DB_PATH), "records": len(list_records())})
            return
        if parsed.path == "/api/records":
            if not self.require_active_subscription():
                return
            self.write_json({"records": list_records()})
            return
        if parsed.path == "/api/search":
            if not self.require_active_subscription():
                return
            query = parse_qs(parsed.query).get("q", [""])[0]
            self.write_json({"records": search_records(query)})
            return
        if parsed.path == "/api/rag/stats":
            if not self.require_active_subscription():
                return
            self.write_json(rag_stats())
            return
        if parsed.path == "/api/connectors/export":
            if not self.require_active_subscription():
                return
            self.write_json(build_connector_export())
            return
        if parsed.path == "/api/account/export":
            self.write_json(build_account_export())
            return
        if parsed.path == "/api/ai/status":
            self.write_json(ai_status())
            return
        if parsed.path == "/api/ai/client-config":
            self.write_json(client_ai_status())
            return
        if parsed.path == "/api/billing/status":
            self.write_json(billing_status())
            return
        if parsed.path == "/api/demo/status":
            self.write_json(demo_status())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            self.handle_login()
            return
        if not self.require_auth():
            return
        if parsed.path == "/api/records":
            if not self.require_active_subscription():
                return
            try:
                payload = self.read_json()
                record = save_record(normalize_record(payload))
                self.write_json({"record": record}, status=201)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/uploads":
            if not self.require_active_subscription():
                return
            try:
                self.write_json({"files": self.save_uploaded_files()}, status=201)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/chat":
            if not self.require_active_subscription():
                return
            try:
                payload = self.read_json()
                self.write_json(query_rag(str(payload.get("question") or "")))
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/ai/client-config":
            if not self.require_active_subscription():
                return
            try:
                payload = self.read_json()
                self.write_json(save_client_ai_config(payload))
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/ai/test":
            if not self.require_active_subscription():
                return
            self.write_json(test_client_ai_config())
            return
        if parsed.path == "/api/billing/sandbox-config":
            try:
                payload = self.read_json()
                self.write_json(save_billing_config(payload))
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/billing/checkout-session":
            try:
                payload = self.read_json()
                result = create_checkout_session(payload)
                self.write_json(result, status=200 if result.get("ok") else 409)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/account/delete-request":
            try:
                payload = self.read_json()
                self.write_json(create_delete_request(payload), status=201)
            except Exception as exc:
                self.write_json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/admin/backup":
            if not self.require_active_subscription():
                return
            try:
                self.write_json(create_runtime_backup(), status=201)
            except Exception as exc:
                self.write_json({"ok": False, "error": str(exc)}, status=500)
            return
        if parsed.path == "/api/admin/rebuild-vector":
            if not self.require_active_subscription():
                return
            result = rebuild_runtime_vector_index()
            self.write_json(result, status=200 if result.get("ok") else 500)
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
        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range", "")
        range_match = re.match(r"bytes=(\d*)-(\d*)$", range_header.strip())

        if range_match:
            start_raw, end_raw = range_match.groups()
            if start_raw == "" and end_raw == "":
                self.send_error(416)
                return
            if start_raw == "":
                suffix_length = int(end_raw)
                start = max(0, file_size - suffix_length)
                end = file_size - 1
            else:
                start = int(start_raw)
                end = int(end_raw) if end_raw else file_size - 1
            end = min(end, file_size - 1)
            if start >= file_size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_cache_headers(file_path)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            self.stream_file(file_path, start=start, length=end - start + 1)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_cache_headers(file_path)
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        self.stream_file(file_path)

    def stream_file(self, file_path: Path, start: int = 0, length: int | None = None) -> None:
        remaining = length
        with file_path.open("rb") as handle:
            if start:
                handle.seek(start)
            while True:
                read_size = STREAM_CHUNK_BYTES if remaining is None else min(STREAM_CHUNK_BYTES, remaining)
                if read_size <= 0:
                    break
                chunk = handle.read(read_size)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                if remaining is not None:
                    remaining -= len(chunk)

    def send_cache_headers(self, file_path: Path) -> None:
        if file_path.name == "reset.html":
            self.send_header("Clear-Site-Data", '"cache"')
        if file_path.suffix.lower() in {".html", ".css", ".js", ".webmanifest"} or file_path.name == "sw.js":
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        elif file_path.suffix.lower() in {".mp4", ".webm", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
            self.send_header("Cache-Control", "public, max-age=86400")

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    connect().close()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Evidentia server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
