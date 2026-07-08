# Evidentia Backup y Restauracion

Fecha: 2026-07-01

## Objetivo vendible

Antes de una demo o piloto fundador, Evidentia debe poder demostrar que el conocimiento del cliente no queda atrapado en una sesion fragil. El minimo vendible es:

- Crear una copia recuperable de la memoria local.
- Comprobar que la copia contiene SQLite, uploads, RAG y derivados.
- Restaurar sin borrar definitivamente el estado anterior.
- No incluir `.env`, claves API ni logs en el backup.

## Que se copia

El script `scripts/evidentia_backup_restore.sh` empaqueta:

- `data/evidentia.sqlite`: registros, entidades, relaciones, evidencias y chunks espejo.
- `data/uploads/`: archivos aportados por el cliente.
- `data/rag/`: indice vectorial compacto local y, si existe, artefactos RAG adicionales.
- `data/derived/`: transcripciones y derivados.
- `data/exports/`: packs generados.

No empaqueta `.env`, logs ni perfiles QA del navegador.

## Crear backup

```bash
scripts/evidentia_backup_restore.sh backup
```

El comando devuelve la ruta del archivo `.tar.gz` creado en `backups/local-node/`.

## Backup del nodo Render

En Render, el backup operativo se ejecuta contra el disco persistente del servicio:

```bash
scripts/render_backup.sh
```

El script crea una copia en `data/backups/render-node/`, ejecuta `verify-restore` sobre el archivo generado y conserva por defecto los ultimos 14 backups. Se puede ajustar con:

```bash
EVIDENTIA_BACKUP_RETENTION=30 scripts/render_backup.sh
```

Este backup protege frente a errores de aplicacion o restauraciones malas dentro del nodo, pero una estrategia de produccion completa debe anadir copia externa cifrada fuera de Render.

## Inspeccionar backup

```bash
scripts/evidentia_backup_restore.sh inspect backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
```

La inspeccion debe mostrar al menos:

- `data/evidentia.sqlite`
- `data/uploads/`
- `data/rag/`

## Verificar restauracion en staging

```bash
scripts/evidentia_backup_restore.sh verify-restore backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
```

Este comando no toca `data/` activo. Extrae el backup en una carpeta temporal, comprueba que existen SQLite, uploads y RAG, y cuenta registros, chunks espejo y evidencias. Para que la demo sea defendible, debe devolver al menos:

```text
RESTORE_CHECK_OK ...
records=3
sqliteChunks=3
evidence=0
```

## Probar copia restaurada arrancando servidor temporal

```bash
scripts/clean_restore_smoke_test.sh backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
```

Este smoke test valida el paso que importa comercialmente: no solo extrae el backup, tambien arranca Evidentia contra una copia temporal mediante `EVIDENTIA_DATA_DIR` y prueba:

- `/api/health`
- `/api/rag/stats`
- `/api/chat` con fuentes
- `/api/connectors/export`

La prueba deja evidencia en `qa/clean-restore/` y no toca `data/` activo.

## Restaurar backup

```bash
scripts/evidentia_backup_restore.sh restore backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
```

La restauracion mueve primero el directorio actual a:

```text
data.before-restore-YYYYMMDDTHHMMSSZ
```

Despues extrae el backup como nuevo `data/`.

## Checklist para piloto

- Parar o cerrar la demo antes de restaurar.
- Crear backup antes de cargar datos reales.
- Inspeccionar el backup creado.
- Ejecutar `verify-restore` antes de prometer recuperacion en una demo.
- Ejecutar `clean_restore_smoke_test.sh` antes de decir que una copia restaurada arranca y responde preguntas.
- Guardar copia externa cifrada si el cliente lo pide.
- Probar restauracion en carpeta/equipo de staging antes de tocar datos reales.
- Confirmar en `/api/health` que el numero de registros coincide.

## Limite comercial

Esto no es todavia instalador completo ni copia externa cifrada. Es el minimo defendible para piloto fundador: copia trazable, inspeccionable y restaurable sin depender de OpenAI. En Render, `scripts/render_backup.sh` deja el nodo preparado para ejecucion recurrente mediante job/cron cuando haya destino externo o politica final de retencion.
