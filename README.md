# Evidentia MVP

Plataforma local-first para crear el espejo vectorial del conocimiento de una persona, equipo, centro u organizacion.

## Incluye

- Ingesta de texto, dictado del navegador y archivos asociados.
- Subida real de archivos al servidor local en `data/uploads/`.
- Indexacion real en ChromaDB persistente bajo `data/rag/chroma/`.
- Extraccion inicial de texto desde TXT, Markdown, HTML, CSV, JSON y PDF.
- Vision local inicial para imagenes y videos: dimensiones, luminosidad, color, detalle y frames extraidos de video.
- Integracion OpenAI opcional mediante `OPENAI_API_KEY` para sintetizar respuestas del chat sobre chunks Chroma.
- Separacion simple de identidad/datos sensibles mediante ID anonimizado.
- Extraccion local de entidades basicas cuando aportan valor: areas, activos, conocimiento, mediciones, resultados y evidencias.
- Mapa visual local de conocimiento en navegador.
- Chat interno conectado a `/api/chat` para preguntar al mapa Chroma y recuperar fuentes.
- Busqueda local sobre los registros guardados.
- API local con SQLite para registros, entidades, evidencias, relaciones y busqueda FTS.
- Fallback a localStorage si se abre como demo estatica sin backend.
- Documento de permisos/consentimiento descargable para datos sensibles e IA agentica.
- Guia de cesion de prueba: `CLINICIAN_TRIAL_GUIDE.md`.
- Arranque local para piloto: `start_evidentia.command`.

## Ejecutar

Modo producto local:

    ./start_evidentia.command

O manualmente:

    .venv/bin/python server.py

Activar OpenAI:

    cp .env.example .env
    # editar .env y poner OPENAI_API_KEY
    ./start_evidentia.command

Abrir:

    http://127.0.0.1:8892/

Modo maqueta estatica:

    python3 -m http.server 8891

Abrir:

    http://127.0.0.1:8891/

## Siguiente paso serio

La base local ya incluye API, SQLite, uploads reales y Chroma persistente. El siguiente paso de produccion es endurecer esta columna vertebral con:

- Postgres para organizaciones, usuarios, datos sensibles separados y permisos.
- Chat RAG conectado a Chroma/pgvector para similitud semantica entre casos, proyectos, notas, fotos, videos, PDF y conocimiento.
- Mapa de conocimiento para conectar fuentes sin imponer estructura obligatoria.
- Pipeline de transcripcion y OCR.
- Permisos por persona, equipo, centro u organizacion.

Ver:

- PRODUCT_BRIEF.md
- CLOUD_ARCHITECTURE.md
