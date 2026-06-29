# Evidentia Backup y Restauracion

Fecha: 2026-06-26

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
- `data/rag/`: indice Chroma local.
- `data/derived/`: transcripciones y derivados.
- `data/exports/`: packs generados.

No empaqueta `.env`, logs ni perfiles QA del navegador.

## Crear backup

```bash
scripts/evidentia_backup_restore.sh backup
```

El comando devuelve la ruta del archivo `.tar.gz` creado en `backups/local-node/`.

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
- Guardar copia externa cifrada si el cliente lo pide.
- Probar restauracion en carpeta/equipo de staging antes de tocar datos reales.
- Confirmar en `/api/health` que el numero de registros coincide.

## Limite comercial

Esto no es todavia instalador completo ni backup automatico programado. Es el minimo manual defendible para piloto fundador: copia local trazable, inspeccionable y restaurable sin depender de OpenAI.
