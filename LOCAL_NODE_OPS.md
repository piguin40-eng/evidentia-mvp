# Evidentia Local Node Ops

## Estado actual

Evidentia corre como servicio local persistente de macOS mediante:

- LaunchAgent: `~/Library/LaunchAgents/com.evidentia.local.plist`
- Proyecto: `/Users/piguin/.openclaw/workspace/evidentia-mvp`
- URL producto: `http://127.0.0.1:8892/`
- URL web comercial: `http://127.0.0.1:8892/website.html`
- Log stdout: `data/evidentia-launchd.out.log`
- Log stderr: `data/evidentia-launchd.err.log`

El archivo privado `.env` contiene `OPENAI_API_KEY` y `OPENAI_MODEL`. No subirlo ni compartirlo.

## Comprobar salud

```bash
curl -sS http://127.0.0.1:8892/api/health
curl -sS http://127.0.0.1:8892/api/ai/status
launchctl print gui/$(id -u)/com.evidentia.local
```

## Backup manual antes de demo o piloto

```bash
scripts/evidentia_backup_restore.sh backup
scripts/evidentia_backup_restore.sh inspect backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
scripts/evidentia_backup_restore.sh verify-restore backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
```

La guia completa esta en `BACKUP_RESTORE.md`. El backup incluye `data/evidentia.sqlite`, `data/uploads/`, `data/rag/`, `data/derived/` y `data/exports/`; no incluye `.env`, claves API ni logs. `verify-restore` restaura en una carpeta temporal y valida registros/chunks sin tocar `data/` activo.

## Reiniciar

```bash
launchctl kickstart -k gui/$(id -u)/com.evidentia.local
```

## Parar temporalmente

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.evidentia.local.plist
```

## Volver a activar

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.evidentia.local.plist
launchctl enable gui/$(id -u)/com.evidentia.local
```

## Nota de producto

Esto es persistencia local para demo/piloto fundador. Antes de venta externa hacen falta:

- Limite de gasto API por piloto.
- Entorno de instalacion reproducible.
- Backup/export de datos probado en equipo externo.
- Avisos legales claros: no vender como software medico.
- Guion demo y oferta piloto cerrada.
