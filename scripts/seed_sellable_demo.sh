#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8892}"

post_record() {
  curl -sS -X POST "${BASE_URL}/api/records" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json' \
    --data-binary @- >/dev/null
}

post_record <<'JSON'
{
  "id": "demo-sepes-estetica-lab-001",
  "createdAt": "2026-06-25T06:35:00Z",
  "date": "2026-06-25",
  "domain": "Estetica dental y laboratorio",
  "recordType": "Caso demo vendible",
  "patientCode": "DEMO-EST-001",
  "hasPrivateIdentity": false,
  "operator": "Yolito Ceram",
  "notes": "Caso ficticio para demo SEPES: rehabilitacion estetica anterior con dos centrales. Se documenta criterio de estratificacion, comunicacion con laboratorio, fotografias iniciales, decision de mockup y resultado esperado. Aprendizaje: cuando el valor L* queda alto en prueba, conviene registrar iluminacion, guia de color y comentario del tecnico para comparar casos futuros. Limite: Evidentia no diagnostica ni prescribe; solo recupera conocimiento propio con fuentes.",
  "entities": [
    {"type": "discipline", "label": "Estetica dental", "confidence": 0.86, "source": "demo"},
    {"type": "knowledge", "label": "Protocolo o aprendizaje", "confidence": 0.82, "source": "demo"},
    {"type": "measurement", "label": "CIELAB", "confidence": 0.78, "source": "demo"},
    {"type": "outcome", "label": "Resultado o seguimiento", "confidence": 0.74, "source": "demo"}
  ],
  "files": []
}
JSON

post_record <<'JSON'
{
  "id": "demo-sepes-operaciones-002",
  "createdAt": "2026-06-25T06:36:00Z",
  "date": "2026-06-25",
  "domain": "Operacion clinica local-first",
  "recordType": "Nota operativa demo",
  "patientCode": "DEMO-OPS-002",
  "hasPrivateIdentity": false,
  "operator": "Pekis Cloud Architect",
  "notes": "Nota ficticia para piloto fundador: la clinica quiere guardar protocolos, incidencias, archivos y decisiones sin depender de memoria humana ni de una nube opaca. Evidentia se presenta como Vector Knowledge Mirror local-first: SQLite para registros, Chroma local para busqueda semantica y export JSON trazable para agentes autorizados. Si OpenAI falla, la demo debe contestar desde RAG local con fuentes o explicar que falta contenido vectorizado.",
  "entities": [
    {"type": "knowledge", "label": "Nota de conocimiento", "confidence": 0.84, "source": "demo"},
    {"type": "pattern", "label": "Patron odontologico", "confidence": 0.71, "source": "demo"},
    {"type": "outcome", "label": "Resultado o seguimiento", "confidence": 0.72, "source": "demo"}
  ],
  "files": []
}
JSON

post_record <<'JSON'
{
  "id": "demo-sepes-formacion-003",
  "createdAt": "2026-06-25T06:37:00Z",
  "date": "2026-06-25",
  "domain": "Formacion y criterio experto",
  "recordType": "Guion demo comercial",
  "patientCode": "DEMO-FORM-003",
  "hasPrivateIdentity": false,
  "operator": "Nora",
  "notes": "Guion ficticio para explicar valor en 10 minutos: primero se guarda una decision o transcripcion, despues se abre el mapa de entidades, luego se pregunta al chat que casos conectan laboratorio, estetica y aprendizaje, y finalmente se muestran fuentes y export. Objecion esperada: esto no es una IA que diagnostica. Respuesta: correcto, es memoria contextual privada para no perder conocimiento propio y consultarlo con trazabilidad.",
  "entities": [
    {"type": "knowledge", "label": "Protocolo o aprendizaje", "confidence": 0.88, "source": "demo"},
    {"type": "discipline", "label": "Estetica dental", "confidence": 0.76, "source": "demo"},
    {"type": "outcome", "label": "Resultado o seguimiento", "confidence": 0.70, "source": "demo"}
  ],
  "files": []
}
JSON

curl -sS "${BASE_URL}/api/health"
printf '\n'
curl -sS "${BASE_URL}/api/rag/stats"
printf '\n'
