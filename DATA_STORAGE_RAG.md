# Evidentia - almacenamiento y RAG

## MVP local

En la version actual, Evidentia funciona como producto local-first dentro de esta carpeta:

`/Users/piguin/.openclaw/workspace/evidentia-mvp`

## Donde se guarda cada cosa

| Elemento | Ubicacion MVP | Funcion |
|---|---|---|
| App | `index.html`, `app.js`, `styles.css`, `server.py` | Interfaz y API local |
| Datos estructurados | `data/evidentia.sqlite` | Casos, entidades, relaciones, evidencias y busqueda FTS |
| Fotos, videos, PDF, STL, DICOM | `data/uploads/` | Carpeta local para binarios del caso |
| RAG vectorial | `data/rag/chroma/` | ChromaDB persistente local |
| Exportaciones | `data/exports/` | Consentimientos, packs e informes descargables |
| Auditoria | `data/audit/` | Logs de acciones, accesos y procesamiento |

## Respuesta clara para explicar al cliente

En el MVP, los datos viven dentro del ordenador/servidor donde se instala Evidentia.

- La informacion estructurada se guarda en SQLite dentro de la propia app.
- Los archivos del caso se guardan en una carpeta local de uploads.
- El RAG vectorial vive en ChromaDB local dentro de `data/rag/chroma/`.
- No hace falta enviar datos a una nube externa para que el MVP funcione localmente.

## Estado RAG actual

- Backend: ChromaDB persistente.
- Coleccion: `evidentia_knowledge`.
- Tabla espejo de chunks: `rag_chunks` en `data/evidentia.sqlite`.
- Cada registro guardado indexa notas del caso y texto extraido de TXT, Markdown, HTML, CSV, JSON y PDF.
- Imagenes: se analizan localmente con dimensiones, orientacion, luminosidad, color medio, calidez, variacion cromatica y detalle/bordes.
- Videos: se extraen frames con ffmpeg, se analizan visualmente y se indexan como texto en Chroma.
- OCR, transcripcion de audio y vision dental semantica quedan como siguiente capa.

## Version cloud

En produccion cloud se mantiene la misma separacion logica:

- Postgres para casos, usuarios, permisos, entidades y relaciones.
- pgvector o Qdrant para embeddings/RAG.
- S3/R2 o almacenamiento equivalente para fotos, videos, PDF y archivos pesados.
- Auditoria por organizacion, usuario, caso y accion.
- Separacion PHI: identidad del paciente separada del conocimiento reutilizable.

## Modelo de instalacion recomendado

### Opcion 1: local-first

La clinica compra Evidentia y se instala un nodo local en su ordenador, NAS o servidor interno.

- Los datos viven dentro de su entorno.
- SQLite/Postgres local guarda la estructura.
- Chroma local guarda el RAG.
- Los archivos viven en carpetas locales.
- Es la opcion mas facil de explicar para privacidad y confianza inicial.

### Opcion 2: cloud

La clinica accede a Evidentia por navegador y todo vive en infraestructura cloud gestionada.

- Postgres/pgvector para datos y embeddings.
- S3/R2 para archivos.
- Mejor para escalado, backups, multiusuario y soporte.
- Requiere contratos, region, seguridad, retencion, permisos y RGPD muy bien cerrados.

### Opcion 3: hibrida recomendada

Primera version vendible recomendada:

- Nodo local en la clinica para datos sensibles, archivos y RAG.
- Cloud opcional para licencia, actualizaciones, backups cifrados, modelos externos autorizados y soporte.
- Los modelos de IA externos solo se usan si el cliente lo permite y si el consentimiento/proveedor esta correctamente configurado.

Frase comercial:

> Evidentia puede instalarse dentro del ordenador o servidor de la clinica, de forma que su conocimiento, archivos y RAG permanezcan bajo su control. Si la clinica quiere nube, se activa una capa cloud segura con permisos, auditoria y contratos de tratamiento de datos.

## Regla de privacidad

No se debe procesar informacion identificable del paciente con modelos de IA externos sin consentimiento informado y sin configurar correctamente proveedor, contrato, region, retencion, seguridad y base juridica.

## Aprendizaje entre clientes

Evidentia no debe quedarse automaticamente con el conocimiento privado de cada clinica.

Modelo correcto:

- Por defecto, cada clinica conserva su conocimiento dentro de su propio nodo local o tenant cloud.
- Evidentia puede recibir telemetria tecnica minima: errores, uso de funciones, rendimiento y salud del sistema.
- Para mejorar modelos, plantillas o protocolos globales, debe existir permiso explicito del cliente.
- El aprendizaje compartido debe ser anonimizado, agregado y sin datos identificables de pacientes, profesionales, equipos o casos.
- El cliente debe poder desactivar esa contribucion.

### Capas posibles

1. **Conocimiento privado del cliente**
   - Vive solo en su nodo o tenant.
   - No se reutiliza para otros clientes.

2. **Patrones anonimizados agregados**
   - Ejemplo: tipos de documentos mas usados, campos frecuentes, errores de captura, necesidades de workflow.
   - Sirve para mejorar producto sin exponer casos.

3. **Biblioteca compartida opt-in**
   - Protocolos, plantillas, prompts, checklists o estructuras que el cliente autoriza compartir.
   - Debe quedar marcado como contribucion voluntaria.

4. **Modelo fundacional/sectorial**
   - Solo con datasets anonimizados, autorizados y revisados legalmente.
   - No debe mezclarse con datos privados sin base juridica.

Frase comercial:

> Cada clinica mantiene su conocimiento privado bajo su control. Evidentia solo aprende de forma global con patrones anonimizados o contenido compartido voluntariamente, nunca apropiandose de casos o datos de pacientes sin permiso.
