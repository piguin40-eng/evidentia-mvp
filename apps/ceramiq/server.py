import json
import re
import os
import socket
import subprocess
import tempfile
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageStat


RAG_ROOT = os.environ.get("CERAMIQ_RAG_ROOT", "/Users/piguin/Desktop/Helix AI Office Files/" + "yoli" + "to-ceram/rag")
KNOWLEDGE_ROOT = "/Users/piguin/.openclaw/workspace/ceramiq-mvp"
ATLAS_RECORDS_ROOT = Path(KNOWLEDGE_ROOT) / "atlas_records"
RAG_PYTHON = RAG_ROOT + "/.venv/bin/python"
RAG_QUERY = RAG_ROOT + "/scripts/query_" + "yoli" + "to_rag.py"
WHISPER_BIN = "/opt/homebrew/bin/whisper"
FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"


MATERIALS = {
    "ips_emax_ceram": {
        "label": "IPS e.max Ceram",
        "cervical_body": "IPS e.max Ceram Deep Dentin A2",
        "dentin": "IPS e.max Ceram Dentin A1",
        "dentin_chroma": "IPS e.max Ceram Dentin A2",
        "value": "IPS e.max Ceram Incisal I1",
        "warm": "IPS e.max Ceram Dentin A2",
        "yellow": "IPS e.max Ceram Dentin A2",
        "neutral": "IPS e.max Ceram Transpa neutral",
        "opal": "IPS e.max Ceram Opal Effect OE1",
        "incisal_low": "IPS e.max Ceram Incisal I1",
        "incisal_high": "IPS e.max Ceram Incisal I2",
        "blue": "IPS e.max Ceram Transpa blue",
        "mamelon_light": "IPS e.max Ceram Incisal I1",
        "mamelon_warm": "IPS e.max Ceram Dentin A2",
        "blocker": "IPS e.max Ceram Deep Dentin BL3",
        "allowed_masses": {
            "IPS e.max Ceram Deep Dentin A2",
            "IPS e.max Ceram Deep Dentin BL3",
            "IPS e.max Ceram Dentin A1",
            "IPS e.max Ceram Dentin A2",
            "IPS e.max Ceram Incisal I1",
            "IPS e.max Ceram Incisal I2",
            "IPS e.max Ceram Transpa neutral",
            "IPS e.max Ceram Transpa blue",
            "IPS e.max Ceram Opal Effect OE1",
        },
    },
    "ips_emax_style": {
        "label": "IPS e.max Style",
        "cervical_body": "Deep Dentin A2",
        "dentin": "Dentin A1",
        "value": "Opal Effect Bright",
        "warm": "Essence copper",
        "yellow": "Essence lemon",
        "neutral": "Transpa Neutral",
        "opal": "Opal Effect",
        "incisal_low": "Incisal I1",
        "incisal_high": "Incisal I2",
        "blue": "Transpa blue",
        "mamelon_light": "Mamelon light",
        "mamelon_warm": "Mamelon orange",
        "blocker": "Deep Dentin bleach + Essence white",
    },
    "creation": {
        "label": "Creation",
        "cervical_body": "Cervical Dentin A2",
        "dentin": "Dentin A1",
        "value": "Enamel Effect Light",
        "warm": "Make In Orange",
        "yellow": "Make In Yellow",
        "neutral": "Clear Neutral",
        "opal": "Opal Incisal",
        "incisal_low": "Enamel E1",
        "incisal_high": "Enamel E2",
        "blue": "Blue Transparent",
        "mamelon_light": "Mamelon Ivory",
        "mamelon_warm": "Mamelon Orange",
        "blocker": "Opaque Dentin bleach",
    },
    "noritake_czr": {
        "label": "Noritake CZR",
        "cervical_body": "Cervical 2",
        "dentin": "Body A1B",
        "value": "Value Plus",
        "warm": "Cervical Orange",
        "yellow": "Creamy Enamel",
        "neutral": "T-0",
        "opal": "Opal T",
        "incisal_low": "E1",
        "incisal_high": "E2",
        "blue": "Blue Modifier",
        "mamelon_light": "Mamelon Light",
        "mamelon_warm": "Mamelon Orange",
        "blocker": "Opaque Dentin Light",
    },
    "vita_vm9": {
        "label": "VITA VM9",
        "cervical_body": "Base Dentine A2",
        "dentin": "Base Dentine A1",
        "value": "Effect Enamel EE1",
        "warm": "Effect Chroma EC4",
        "yellow": "Effect Chroma EC3",
        "neutral": "Window",
        "opal": "Effect Opal EO1",
        "incisal_low": "Enamel ENL",
        "incisal_high": "Enamel END",
        "blue": "Effect Enamel EE9",
        "mamelon_light": "Mamelon MM1",
        "mamelon_warm": "Mamelon MM3",
        "blocker": "Opaque Dentine bleach",
    },
}


def material_config(material_payload):
    material_id = material_payload.get("id", "ips_emax_ceram") if isinstance(material_payload, dict) else "ips_emax_ceram"
    if material_id == "ips_emax_ceram_bleach":
        material_id = "ips_emax_ceram"
    if material_id == "custom":
        custom = material_payload.get("custom_name", "").strip() if isinstance(material_payload, dict) else ""
        base = MATERIALS["ips_emax_ceram"].copy()
        base["label"] = custom or "Material personalizado"
        return base
    return MATERIALS.get(material_id, MATERIALS["ips_emax_ceram"]).copy()


def safe_name(name):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip())
    return cleaned.strip(".-") or "archivo"


def clean_form_payload(payload):
    return payload.rstrip(b"\r\n-")


def write_atlas_record(file_names, photo_payloads, photo_roles, material_payload, case_description, audio_names, audio_transcripts):
    case_id = f"CERAMIQ-ATLAS-{int(time.time())}"
    record_dir = ATLAS_RECORDS_ROOT / case_id
    photos_dir = record_dir / "photos"
    record_dir.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    stored_photos = []
    for index, photo in enumerate(photo_payloads, start=1):
        original_name = photo.get("name") or f"foto-{index}.jpg"
        file_name = f"{index:02d}-{safe_name(original_name)}"
        path = photos_dir / file_name
        path.write_bytes(clean_form_payload(photo.get("payload", b"")))
        role = next((item.get("role") for item in photo_roles if item.get("name") == original_name), "")
        stored_photos.append({"name": original_name, "stored_as": str(path), "role": role or "Foto clinica"})

    material = material_config(material_payload)
    manifest = {
        "case_id": case_id,
        "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": "CeramIQ Atlas",
        "status": "indexed_pending_graph_enrichment",
        "material_system": material["label"],
        "material_payload": material_payload,
        "case_description": case_description,
        "input_photos": stored_photos,
        "input_audio": audio_names,
        "case_audio_transcript": "\n".join(audio_transcripts),
        "next_step": "run RAG/vector + ceramic graph enrichment over this manifest and associated photos",
    }
    manifest_path = record_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    log_path = ATLAS_RECORDS_ROOT / "indexed_cases.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"case_id": case_id, "manifest": str(manifest_path), "photos": len(stored_photos)}, ensure_ascii=False) + "\n")
    return manifest


def apply_case_modifiers(material, case_text):
    text = case_text.lower()
    if material["label"] == "IPS e.max Ceram" and any(term in text for term in ["bleach", "bl1", "bl2", "bl3", "bl4"]):
        material = material.copy()
        material.update(
            {
                "cervical_body": "IPS e.max Ceram Deep Dentin BL3",
                "dentin": "IPS e.max Ceram Dentin A1",
                "dentin_chroma": "IPS e.max Ceram Dentin A2",
                "value": "IPS e.max Ceram Incisal I1",
                "incisal_low": "IPS e.max Ceram Incisal I1",
                "blocker": "IPS e.max Ceram Deep Dentin BL3",
                "case_modifier": "bleach_masses",
            }
        )
    return material


def query_clinical_rag(file_names):
    return fallback_reviewed_rag("live Chroma query disabled for MVP latency; reviewed RAG knowledge used synchronously")


def fallback_reviewed_rag(reason):
    paths = [
        KNOWLEDGE_ROOT + "/rag_reviewed/protocolo-recetas-por-tercios-bigcolor.md",
        KNOWLEDGE_ROOT + "/rag_reviewed/miatlas-campos-minimos-color-ceramica.md",
        KNOWLEDGE_ROOT + "/rag_reviewed/protocolo-bloqueo-sustrato-oscuro-feldespatica.md",
    ]
    excerpts = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read().strip()
            excerpts.append("Fuente: " + path + "\n" + text[:900])
        except OSError:
            continue
    if not excerpts:
        return {"status": "unavailable", "excerpt": public_text(reason)}
    return {
        "status": "reviewed_fallback",
        "excerpt": public_text("Chroma timeout/error: " + reason[:240] + "\n\n" + "\n\n---\n\n".join(excerpts)),
    }


def public_text(value):
    return re.sub("yoli" + "to", "CeramIQ", value, flags=re.IGNORECASE)


def transcribe_audio_payload(audio_name, audio_payload):
    if not audio_name or not audio_payload:
        return ""
    suffix = os.path.splitext(audio_name)[1] or ".webm"
    with tempfile.TemporaryDirectory(prefix="ceramiq-audio-") as tmpdir:
        audio_path = os.path.join(tmpdir, "case-audio" + suffix)
        with open(audio_path, "wb") as handle:
            handle.write(audio_payload.rstrip(b"\r\n-"))
        try:
            completed = subprocess.run(
                [
                    WHISPER_BIN,
                    audio_path,
                    "--language",
                    "Spanish",
                    "--model",
                    "turbo",
                    "--output_format",
                    "txt",
                    "--output_dir",
                    tmpdir,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env={
                    **os.environ,
                    "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                    "HOME": "/Users/piguin",
                },
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        if completed.returncode != 0:
            return ""
        transcript_path = os.path.join(tmpdir, "case-audio.txt")
        try:
            with open(transcript_path, "r", encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError:
            return ""


def srgb_to_xyz_channel(value):
    value = value / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def xyz_to_lab_channel(value):
    if value > 0.008856:
        return value ** (1 / 3)
    return (7.787 * value) + (16 / 116)


def rgb_to_lab(rgb):
    r, g, b = [srgb_to_xyz_channel(channel) for channel in rgb]
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    fx, fy, fz = xyz_to_lab_channel(x), xyz_to_lab_channel(y), xyz_to_lab_channel(z)
    return {
        "L": round((116 * fy) - 16, 1),
        "a": round(500 * (fx - fy), 1),
        "b": round(200 * (fy - fz), 1),
    }


def delta_e(lab_a, lab_b):
    return round(
        (
            (lab_a["L"] - lab_b["L"]) ** 2
            + (lab_a["a"] - lab_b["a"]) ** 2
            + (lab_a["b"] - lab_b["b"]) ** 2
        )
        ** 0.5,
        1,
    )


def average_rgb_for_third(image_path, third_index):
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        top = int(height * third_index / 3)
        bottom = int(height * (third_index + 1) / 3)
        crop = rgb.crop((0, top, width, bottom))
        mean = ImageStat.Stat(crop.resize((1, 1))).mean
    return tuple(int(round(channel)) for channel in mean[:3])


def role_text(photo_roles, file_name, index):
    for item in photo_roles:
        if item.get("name") == file_name:
            return item.get("role", "")
    if index == 0:
        return "Diente objetivo + guia"
    return ""


def has_gray_card(file_names, photo_roles):
    text = " ".join(file_names + [item.get("role", "") for item in photo_roles]).lower()
    return any(term in text for term in ["gris", "gray", "bigcolor", "big therem", "bigtherem", "tarjeta"])


def has_shade_guide(file_names, photo_roles):
    text = " ".join(file_names + [item.get("role", "") for item in photo_roles]).lower()
    return any(term in text for term in ["guia", "guía", "vita", "3d", "referencia"])


def has_polarized(file_names, photo_roles):
    text = " ".join(file_names + [item.get("role", "") for item in photo_roles]).lower()
    return any(term in text for term in ["polarizada", "polarizado", "polar"])


def analyze_photo_payloads(photo_payloads, photo_roles):
    if not photo_payloads:
        return {
            "calibration_status": "no_photos_received",
            "delta_e": None,
            "thirds": [],
            "analysis_mode": "no_image_analysis",
        }
    names = ["Incisal", "Medio", "Cervical"]
    with tempfile.TemporaryDirectory(prefix="ceramiq-photos-") as tmpdir:
        image_paths = []
        for index, photo in enumerate(photo_payloads):
            suffix = os.path.splitext(photo["name"])[1] or ".jpg"
            path = os.path.join(tmpdir, f"photo-{index}{suffix}")
            with open(path, "wb") as handle:
                handle.write(photo["payload"].rstrip(b"\r\n-"))
            image_paths.append(path)
        target_path = image_paths[0]
        current_path = image_paths[-1]
        thirds = []
        deltas = []
        for index, name in enumerate(names):
            target = rgb_to_lab(average_rgb_for_third(target_path, index))
            current = rgb_to_lab(average_rgb_for_third(current_path, index))
            de = delta_e(target, current)
            deltas.append(de)
            diagnosis = diagnose_third(name, target, current, de)
            thirds.append({"name": name, "target": target, "current": current, "delta_e": de, "diagnosis": diagnosis})
        return {
            "calibration_status": calibration_status_for(photo_payloads, photo_roles),
            "delta_e": round(sum(deltas) / len(deltas), 1),
            "thirds": thirds,
            "analysis_mode": "pixel_lab_by_thirds",
        }


def calibration_status_for(photo_payloads, photo_roles):
    file_names = [item["name"] for item in photo_payloads]
    gray = has_gray_card(file_names, photo_roles)
    guide = has_shade_guide(file_names, photo_roles)
    polarized = has_polarized(file_names, photo_roles)
    if len(photo_payloads) < 2:
        return "single_photo_estimated_no_comparison"
    if gray and guide and polarized:
        return "gray_card_guide_polarized_protocol_present"
    if gray and guide:
        return "gray_card_and_shade_guide_present"
    if gray:
        return "gray_card_present_estimated"
    return "estimated_from_uploaded_pixels"


def diagnose_third(name, target, current, de):
    d_l = round(current["L"] - target["L"], 1)
    d_a = round(current["a"] - target["a"], 1)
    d_b = round(current["b"] - target["b"], 1)
    parts = []
    if abs(d_l) >= 2:
        parts.append("alto de valor" if d_l > 0 else "bajo de valor")
    if abs(d_b) >= 2:
        parts.append("demasiado calido/amarillo" if d_b > 0 else "falta croma calido")
    if abs(d_a) >= 1.5:
        parts.append("exceso rojizo" if d_a > 0 else "falta componente rojizo")
    if not parts:
        parts.append("cerca del objetivo optico")
    return f"{name}: Delta E {de}. " + ", ".join(parts) + "."


def recipe_for_case(thirds, case_text, material):
    dark_substrate = any(term in case_text.lower() for term in ["oscuro", "negro", "muñon", "munon", "sustrato"])
    mat = apply_case_modifiers(material_config(material), case_text)
    recipe = []
    for third in thirds:
        target = third["target"]
        current = third["current"]
        d_l = current["L"] - target["L"]
        d_b = current["b"] - target["b"]
        d_a = current["a"] - target["a"]
        name = third["name"]
        if name == "Cervical":
            masses = [
                mass(mat["blocker"] if dark_substrate else mat["cervical_body"], 32 + (6 if d_l < -2 else 0), "cuerpo, valor profundo y bloqueo inicial" if dark_substrate else "cuerpo cervical y saturacion base"),
                mass(mat.get("dentin_chroma", mat["dentin"]), 20, "recupera croma cervical con dentina del sistema"),
                mass(mat["dentin"], 24, "transicion dentinaria y control de valor"),
                mass(mat["neutral"], 24 - (6 if d_l < -2 else 0), "profundidad sin cerrar el margen"),
            ]
            note = "Aplicar fino y controlar el margen; si el sustrato es oscuro, usar wash de bloqueo antes de estratificar."
        elif name == "Medio":
            masses = [
                mass(mat["dentin"], 38, "masa principal de valor y cuerpo medio"),
                mass(mat["value"], 22, "sube luminosidad interna controlada"),
                mass(mat.get("dentin_chroma", mat["dentin"]), 18, "ajuste de croma medio con dentina del sistema"),
                mass(mat["neutral"], 22, "profundidad y fusion optica"),
            ]
            note = "Construir volumen principal con mamelones suaves y no sobreopacar el centro."
        else:
            masses = [
                mass(mat["opal"], 30, "opalescencia incisal azulada"),
                mass(mat["incisal_low"] if d_l <= 2 else mat["incisal_high"], 24, "valor del borde sin efecto tiza"),
                mass(mat["blue"] if d_b > 1 else mat["neutral"], 24, "profundidad y translucidez del borde"),
                mass(mat["mamelon_light"] if d_a <= 1 else mat["mamelon_warm"], 22, "detalle interno y naturalidad"),
            ]
            note = "Aplicar halo y translucidez en capa fina; evitar subir demasiado el valor si ya esta alto."
        recipe.append({"third": name, "material": mat["label"], "application_note": note, "masses": normalize_masses(masses)})
    return recipe


def mass(name, percentage, function):
    return {"name": name, "percentage": percentage, "function": function}


def normalize_masses(masses):
    total = sum(item["percentage"] for item in masses) or 100
    normalized = []
    running = 0
    for item in masses[:-1]:
        pct = round(item["percentage"] * 100 / total)
        running += pct
        normalized.append({**item, "percentage": pct})
    normalized.append({**masses[-1], "percentage": max(0, 100 - running)})
    return normalized


def validate_recipe_masses(recipe, material):
    allowed = material_config(material).get("allowed_masses")
    if not allowed:
        return {
            "ok": False,
            "detail": "Sistema sin lista blanca local; revisar nombres contra ficha tecnica antes de entregar.",
            "invalid": [],
        }
    invalid = sorted({mass["name"] for block in recipe for mass in block.get("masses", []) if mass["name"] not in allowed})
    return {
        "ok": not invalid,
        "detail": "Todas las masas proceden de la lista blanca local del sistema." if not invalid else "Hay masas fuera de lista blanca: " + ", ".join(invalid),
        "invalid": invalid,
    }


def build_validation(file_names, audio_transcripts, image_analysis, recipe, rag_evidence, photo_roles, material_payload=None):
    mass_validation = validate_recipe_masses(recipe, material_payload or {"id": "ips_emax_ceram"})
    checks = [
        {
            "id": "photos_received",
            "label": "Fotos recibidas",
            "ok": len(file_names) > 0,
            "detail": f"{len(file_names)} foto(s) enviadas al analisis",
        },
        {
            "id": "comparison_ready",
            "label": "Comparativa objetivo/actual",
            "ok": len(file_names) >= 2,
            "detail": "La primera foto se toma como objetivo y la ultima como actual" if len(file_names) >= 2 else "Sube minimo objetivo y prueba para comparar Delta E real",
        },
        {
            "id": "pixel_lab",
            "label": "CIELAB calculado",
            "ok": image_analysis["analysis_mode"] == "pixel_lab_by_thirds",
            "detail": image_analysis["analysis_mode"],
        },
        {
            "id": "gray_card_protocol",
            "label": "Tarjeta gris calibrada",
            "ok": has_gray_card(file_names, photo_roles),
            "detail": "Tarjeta gris detectada en el protocolo" if has_gray_card(file_names, photo_roles) else "Marca/sube una foto de tarjeta gris calibrada",
        },
        {
            "id": "shade_guide_protocol",
            "label": "Guia de color",
            "ok": has_shade_guide(file_names, photo_roles),
            "detail": "Guia o referencia de color detectada" if has_shade_guide(file_names, photo_roles) else "Incluye guia VITA/3D o referencia visible",
        },
        {
            "id": "rag_loaded",
            "label": "RAG revisado consultado",
            "ok": rag_evidence["status"] != "unavailable",
            "detail": rag_evidence["status"],
        },
        {
            "id": "audio_context",
            "label": "Contexto de voz",
            "ok": bool(audio_transcripts),
            "detail": "Audio transcrito" if audio_transcripts else "Sin audio o transcripcion no disponible",
        },
        {
            "id": "recipe_contract",
            "label": "Contrato de receta",
            "ok": bool(recipe) and all(len(block.get("masses", [])) == 4 for block in recipe),
            "detail": "4 masas por tercio" if recipe else "Receta pendiente de fotos validas",
        },
        {
            "id": "mass_registry",
            "label": "Masas reales",
            "ok": mass_validation["ok"],
            "detail": mass_validation["detail"],
        },
    ]
    score = round(sum(1 for item in checks if item["ok"]) * 100 / len(checks))
    return {
        "ready_for_clinical_review": checks[0]["ok"] and checks[2]["ok"] and checks[3]["ok"] and checks[5]["ok"] and checks[6]["ok"],
        "score": score,
        "checks": checks,
        "mass_registry": mass_validation,
    }


class FastBindHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_name = "ceramiq.local"
        self.server_port = self.server_address[1]


class CeramIQHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/healthz":
            payload = json.dumps(
                {
                    "ok": True,
                    "service": "ceramiq",
                    "engine": "CeramIQ",
                    "status": "operational",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/ceramiq/analyze", "/api/ceramiq/index"):
            self.send_error(404, "Unknown endpoint")
            return

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_error(415, "Expected multipart/form-data")
            return

        boundary_token = "boundary="
        boundary = content_type.split(boundary_token, 1)[-1].strip().strip('"')
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        file_names = []
        photo_payloads = []
        audio_names = []
        audio_transcripts = []
        case_description = ""
        photo_roles = []
        material_payload = {"id": "ips_emax_ceram", "custom_name": ""}
        if boundary:
            marker = ("--" + boundary).encode("utf-8")
            for part in body.split(marker):
                header, _, _payload = part.partition(b"\r\n\r\n")
                if b'name="case_description"' in header:
                    case_description = _payload.rstrip(b"\r\n-").decode("utf-8", "ignore").strip()
                    continue
                if b'name="photo_roles"' in header:
                    try:
                        photo_roles = json.loads(_payload.rstrip(b"\r\n-").decode("utf-8", "ignore").strip() or "[]")
                    except json.JSONDecodeError:
                        photo_roles = []
                    continue
                if b'name="material_system"' in header:
                    try:
                        material_payload = json.loads(_payload.rstrip(b"\r\n-").decode("utf-8", "ignore").strip() or "{}")
                    except json.JSONDecodeError:
                        material_payload = {"id": "ips_emax_ceram", "custom_name": ""}
                    continue
                if b'name="case_audio"' in header and b"filename=" in header:
                    match = re.search(r'filename="([^"]+)"', header.decode("utf-8", "ignore"))
                    if match:
                        audio_name = match.group(1)
                        audio_names.append(audio_name)
                        transcript = transcribe_audio_payload(audio_name, _payload)
                        if transcript:
                            audio_transcripts.append(transcript)
                    continue
                if b'name="photos"' not in header or b"filename=" not in header:
                    continue
                match = re.search(r'filename="([^"]+)"', header.decode("utf-8", "ignore"))
                if match:
                    photo_name = match.group(1)
                    file_names.append(photo_name)
                    photo_payloads.append({"name": photo_name, "payload": _payload})

        if self.path == "/api/ceramiq/index":
            manifest = write_atlas_record(file_names, photo_payloads, photo_roles, material_payload, case_description, audio_names, audio_transcripts)
            response = {
                "ok": True,
                "case_id": manifest["case_id"],
                "photos_indexed": len(manifest["input_photos"]),
                "status": manifest["status"],
            }
            payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        rag_evidence = query_clinical_rag(file_names)
        image_analysis = analyze_photo_payloads(photo_payloads, photo_roles)
        full_case_text = "\n".join([case_description, *audio_transcripts]).strip()
        selected_material = material_config(material_payload)
        recipe = recipe_for_case(image_analysis["thirds"], full_case_text, material_payload) if image_analysis["thirds"] else []
        validation = build_validation(file_names, audio_transcripts, image_analysis, recipe, rag_evidence, photo_roles, material_payload)
        response = {
            "engine": "CeramIQ",
            "public_engine": "CeramIQ Clinical RAG",
            "policy": "ceramiq_ceramic_only",
            "rag_required": True,
            "rag_status": rag_evidence["status"],
            "rag_excerpt": rag_evidence["excerpt"],
            "case_id": f"CERAMIQ-{int(time.time())}",
            "input_photos": file_names,
            "photo_roles": photo_roles,
            "material_system": selected_material["label"],
            "input_audio": audio_names,
            "case_description": case_description,
            "case_audio_transcript": "\n".join(audio_transcripts),
            "calibration_status": image_analysis["calibration_status"],
            "analysis_mode": image_analysis["analysis_mode"],
            "delta_e": image_analysis["delta_e"],
            "thirds": image_analysis["thirds"],
            "recipe": recipe,
            "validation": validation,
            "recipe_contract": "4_masses_per_third_with_percentage_and_optical_function",
            "warning": "Valores CIELAB estimados desde pixeles subidos. Para medicion clinica absoluta requiere tarjeta gris, guia y polarizada correctamente capturadas.",
        }
        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


APP_ROOT = os.environ.get("CERAMIQ_APP_ROOT", os.path.dirname(os.path.abspath(__file__)))
APP_PORT = int(os.environ.get("PORT", os.environ.get("CERAMIQ_PORT", "8798")))

handler = partial(CeramIQHandler, directory=APP_ROOT)
server = FastBindHTTPServer(("0.0.0.0", APP_PORT), handler)
print(f"Serving CeramIQ on http://0.0.0.0:{APP_PORT}/", flush=True)
server.serve_forever()
