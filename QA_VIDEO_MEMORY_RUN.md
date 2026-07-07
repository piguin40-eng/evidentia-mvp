# Evidentia QA - Video Memory

Fecha: 2026-06-22
Responsable: piguin

## Objetivo

Validar que Evidentia puede recibir audio/video propio o autorizado, transcribirlo localmente e indexarlo en el RAG.

## Prueba Ejecutada

Entrada usada:

- Audio OGG real recibido por Telegram: bb69635f-89af-4f5e-8a29-4f52dd99faf9.ogg

Flujo:

1. Upload via /api/uploads.
2. Registro creado via /api/records.
3. Backend ejecuto ffmpeg para extraer WAV.
4. Backend ejecuto Whisper CLI para transcribir.
5. Transcripcion JSON/TXT generada en data/derived/transcripts/.
6. Texto con timestamps indexado por el flujo existente de Chroma.

## Resultado

- Upload: OK.
- Registro QA: qa-video-memory-20260622-audio.
- ragChunks del registro: 2.
- Chroma total antes de prueba: 7 chunks.
- Chroma total despues de prueba: 9 chunks.
- Estado: PASS.

## Evidencia Generada

- Audio subido: data/uploads/20260622195711_09f0c8254924_bb69635f-89af-4f5e-8a29-4f52dd99faf9.ogg
- Audio derivado: data/derived/audio/e3698db2b70cfc3790a2ab3d_bb69635f-89af-4f5e-8a29-4f52dd99faf9.wav
- Transcripcion JSON: data/derived/transcripts/e3698db2b70cfc3790a2ab3d_bb69635f-89af-4f5e-8a29-4f52dd99faf9.json
- Transcripcion TXT: data/derived/transcripts/e3698db2b70cfc3790a2ab3d_bb69635f-89af-4f5e-8a29-4f52dd99faf9.txt

## Limitaciones

- Whisper CLI tarda en CPU; para videos largos hace falta cola/job asincrono.
- La UI todavia no muestra barra de progreso por fases.
- Falta boton o estado visible de transcripcion para usuario final.
- Falta QA con video MP4 real, no solo audio.
- YouTube debe quedar detras de permisos/derechos o transcripcion autorizada.

## Siguiente Mejora

Crear estado visible en UI:

- Upload recibido.
- Extrayendo audio.
- Transcribiendo.
- Indexando.
- Listo para preguntar.
