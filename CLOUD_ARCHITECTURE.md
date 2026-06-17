# Evidentia Cloud Architecture v1

## Version de producto

La version cloud debe sustituir la persistencia local por una arquitectura con API, base de datos, almacenamiento de archivos, embeddings, grafo y auditoria.

## Pipeline

```text
Audio / texto / PDF / foto / nota
  -> intake API
  -> storage bruto
  -> transcripcion u OCR
  -> normalizacion
  -> separacion PHI
  -> extraccion de entidades
  -> relaciones de grafo
  -> embeddings
  -> indices de busqueda
  -> consulta trazable
```

## Servicios

- Frontend: app web responsive para clinica, laboratorio y admin.
- API: autenticacion, ingesta, consulta, casos, archivos, grafo y auditoria.
- Worker: transcripcion, OCR, embeddings, extraccion de entidades y jobs largos.
- Database: Postgres para registros, entidades, relaciones, usuarios, permisos y auditoria.
- Object storage: audios, imagenes, PDF, STL, escaneos y adjuntos.
- Vector store: pgvector, Qdrant o similar para similitud semantica.
- Graph layer: tablas relacionales especializadas al inicio; Neo4j/RedisGraph solo si el volumen lo exige.

## Esquema minimo

- organizations
- users
- patients_phi
- cases
- records
- files
- entities
- relations
- embeddings
- audit_events
- access_grants

## Separacion PHI

`patients_phi` contiene identidad sensible. El conocimiento reusable debe apuntar a `patient_code` o `case_id` anonimo.

Regla: una consulta tecnica no debe necesitar leer PHI salvo permiso explicito y contexto clinico necesario.

## Endpoints v1

- `POST /api/intake/text`
- `POST /api/intake/audio`
- `POST /api/intake/file`
- `GET /api/records`
- `GET /api/records/{id}`
- `GET /api/search?q=`
- `GET /api/graph?case_id=`
- `POST /api/query`
- `GET /api/audit`

## Respuesta de consulta

Toda respuesta debe devolver:

- `answer`
- `confidence`
- `records_used`
- `relations_used`
- `evidence`
- `missing_data`

## Stack recomendado para Pekis

- FastAPI o Node/NestJS para API.
- Postgres + pgvector para primera version.
- S3/R2 para archivos.
- Redis/queue para jobs.
- Whisper o proveedor STT para audio.
- Modelo extractor con schema JSON estricto.
- OpenTelemetry/logs de auditoria.

## Criterio de salida a mercado

La primera version vendible no necesita IA perfecta. Si necesita:

- Captura facil.
- Guardado persistente real.
- Busqueda rapida.
- Entidades y relaciones visibles.
- Exportacion del caso.
- Seguridad basica por organizacion.
- Trazabilidad de fuente.
