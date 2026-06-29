# Evidentia - despliegue estable para companeros

Objetivo: que Evidentia no dependa del Mac de Miguel y pueda usarse por companeros con acceso controlado.

## Arquitectura minima v0

- VPS o servidor siempre encendido.
- Docker Compose.
- Volumen persistente `./data:/app/data` para SQLite, uploads, Chroma, exports y derivados.
- Backups de `data/` usando `scripts/evidentia_backup_restore.sh`.
- HTTPS delante del contenedor.
- Autenticacion externa recomendada: Cloudflare Access, Tailscale ACL o reverse proxy con SSO.
- Autenticacion interna opcional: `EVIDENTIA_BASIC_AUTH_USER` y `EVIDENTIA_BASIC_AUTH_PASSWORD`.

## Primer despliegue

```bash
cp .env.production.example .env.production
# editar .env.production y poner una clave larga
docker compose up -d --build
curl -fsS http://127.0.0.1:8892/api/healthz
```

Abrir:

```text
http://SERVIDOR:8892/
```

En produccion real no dejar `8892` abierto a Internet sin HTTPS y login.

## Backup

```bash
docker compose exec evidentia bash -lc 'scripts/evidentia_backup_restore.sh backup'
```

## Restauracion

Parar primero el servicio:

```bash
docker compose down
scripts/evidentia_backup_restore.sh verify-restore backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
scripts/evidentia_backup_restore.sh restore backups/local-node/evidentia-data-YYYYMMDDTHHMMSSZ.tar.gz
docker compose up -d
```

## Regla de seguridad

No mezclar datos de varios clientes/companeros en una sola instancia sin usuarios, permisos y separacion por organizacion. Para piloto interno pequeno se puede usar una instancia compartida con login, pero cada cliente externo debe tener nodo/base separados hasta implementar multi-tenant real.
