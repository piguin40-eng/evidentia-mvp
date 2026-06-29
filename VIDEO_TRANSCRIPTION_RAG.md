# Evidentia - video transcription to RAG

Fuente: idea de Miguel, 2026-06-22.

## Tesis

Evidentia debe poder convertir video y audio del cliente en conocimiento consultable:

1. El usuario sube un video/audio propio o autorizado.
2. Evidentia extrae el audio.
3. Transcribe con Whisper/STT.
4. Divide la transcripcion en chunks con timestamps.
5. Indexa texto, fuente, tiempo y metadatos en el RAG del cliente.
6. Permite preguntar: que dijo sobre X, resume las decisiones, extrae pasos o convierte esto en protocolo.

## Casos De Uso

- Cliente sube una clase, curso, reunion, webinar, demo o explicacion propia.
- Profesional guarda un video de criterio tecnico y lo convierte en memoria consultable.
- Equipo importa una grabacion interna para recuperar decisiones.
- YouTube/public web solo cuando el usuario tenga derecho a procesar ese contenido o aporte una transcripcion/licencia adecuada.

## Flujo MVP

1. Upload local de .mp4, .mov, .m4a, .mp3, .wav u .ogg.
2. ffmpeg extrae audio normalizado.
3. Whisper local transcribe.
4. Guardar:
   - archivo original en data/uploads/
   - audio extraido en data/derived/audio/
   - transcripcion en data/derived/transcripts/
   - chunks en SQLite y Chroma
5. Cada chunk debe incluir:
   - registro/caso/proyecto
   - archivo origen
   - timestamp inicio/fin
   - texto
   - idioma
   - confianza si el proveedor la ofrece
   - origen: propio, autorizado, publico, desconocido

## YouTube

YouTube debe tratarse con cautela:

- Opcion segura v1: el usuario pega una transcripcion propia o autorizada.
- Opcion v1.5: importar subtitulos disponibles cuando el uso sea permitido.
- Opcion v2: descarga/procesado de video con confirmacion explicita de que el usuario tiene derecho a procesarlo.

No convertir Evidentia en herramienta para extraer contenido ajeno sin permiso. El valor vendible es crear memoria propia del cliente, no piratear conocimiento externo.

## Producto

Nombre del modulo:

- Evidentia Video Memory

Promesa:

> Sube una clase, reunion o video propio y Evidentia lo convierte en memoria consultable con fuentes y marcas de tiempo.

## Requisitos De Calidad

- Mostrar progreso: extrayendo audio, transcribiendo, indexando, listo.
- Permitir revisar y editar transcripcion antes de indexarla si el cliente quiere maxima precision.
- Mantener timestamps clicables o referenciables.
- Marcar incertidumbre cuando el audio sea malo.
- No vender la transcripcion como perfecta.
- Permitir borrar original, audio derivado y chunks asociados.

## Riesgos

- Coste y tiempo en videos largos.
- Derechos de autor si se procesan videos externos.
- Datos sensibles en reuniones o pacientes.
- Whisper puede fallar con ruido, acentos, solapamientos o terminologia tecnica.
- La transcripcion mala contamina el RAG si no se marca confianza.

## Prioridad

Alta para Evidentia vendible, porque convierte una necesidad facil de entender en valor inmediato:

- Dame tus videos, audios, clases o reuniones y los convierto en conocimiento buscable.

MVP recomendado:

1. Upload local de video/audio.
2. Transcripcion Whisper local.
3. Chunks con timestamps.
4. Indexacion en RAG.
5. Consulta con fuente y tiempo.
