# AbutmentIQ

Aplicación de revisión humana supervisada para mallas dentales STL/PLY.

## Estado de seguridad

- La predicción es experimental y nunca constituye una decisión clínica autónoma.
- La revisión humana prevalece, se persiste append-only y se atribuye al principal autenticado; el navegador no puede suministrar otra identidad de revisor.
- Las correcciones crean candidatos de aprendizaje; no hay reentrenamiento ni promoción automática.
- La ingesta de plataformas falla cerrada sin token Bearer.
- Paciente, clínica, pedido y evento de origen se conservan en una bóveda privada cifrada, separada de la geometría pseudonimizada.
- No existe envío automático de correo. Cualquier comunicación futura requiere validación y aprobación humana.

## Plataformas preparadas

Contrato común para `medit`, `3shape`, `exocad`, `itero` y `generic`:

```text
conector local de solo lectura
→ archivo STL/PLY estable
→ POST autenticado /api/platform-intake/mesh
→ SHA-256 + identidad geométrica
→ cola continua
→ revisión humana
→ candidato de entrenamiento append-only
```

La existencia del contrato no afirma que exista una API oficial habilitada para cada plataforma. El adaptador concreto debe verificarse con el producto/licencia y la exportación autorizada del laboratorio.

## Desarrollo local

Requisitos: Node 22, Python 3.11 y `uv`.

```bash
npm ci
uv sync
uv run python scripts/build_bootstrap_assets.py
npm run build
uv run pytest -q
npm test -- --run
npm run lint
npm run backend
```

`.env.local` es privado y no se publica. `.env.example` contiene únicamente nombres de variables.

## Render

`render.yaml` crea un único servicio Docker de pago con:

- autenticación HTTP Basic obligatoria para la aplicación;
- tokens independientes para ingesta e identidad;
- disco persistente de 10 GB montado en `/var/data/abutmentiq`;
- un solo worker para conservar las garantías de bloqueo de archivos;
- activos de demostración y modelo bootstrap completamente sintéticos;
- health check en `/healthz`.

Según la documentación de Render consultada el 20-08-2026, los discos persistentes están cifrados en reposo, reciben snapshots automáticos diarios disponibles al menos siete días, solo pueden adjuntarse a una instancia y desactivan los despliegues sin interrupción. Esta fase es adecuada para una implantación inicial controlada; el escalado posterior debe mover eventos, identidad y cola a almacenamiento gestionado transaccional.

## Secretos

No introducir secretos en Git ni en el chat. Render genera los valores iniciales declarados con `generateValue: true`. La contraseña del visor debe recuperarse o rotarse desde el panel protegido de Render.

## Datos excluidos

`.gitignore` y `.dockerignore` excluyen:

- `runtime/`, colas y JSONL;
- bases de datos;
- `.env*` salvo `.env.example`;
- mallas clínicas de demostración locales;
- modelos/manifiestos clínicos locales;
- dependencias y builds.
