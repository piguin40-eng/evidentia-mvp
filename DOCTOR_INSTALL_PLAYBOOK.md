# Evidentia Local Node - Playbook De Instalacion Para Doctor

Fecha: 2026-06-27

## Objetivo

Instalar Evidentia como memoria IA privada del doctor o centro:

- Sus datos quedan en su ordenador, servidor o NAS.
- Su conocimiento es suyo.
- Su IA/API la paga el doctor si quiere sintesis externa.
- Miguel/Helix cobra instalacion y soporte, no tokens del cliente.

## Mensaje Para El Doctor

Usa esta explicacion simple:

> Te instalo Evidentia Local Node: una memoria privada para tu conocimiento profesional. Guardas protocolos, PDFs, fotos, audios, decisiones, errores y aprendizajes. Luego puedes buscar y preguntar sobre ese conocimiento con fuentes. Los datos quedan en tu entorno. Si quieres conectarlo a IA externa, usamos tu propia API, pagada por ti. Yo no me quedo tus datos ni pago tus tokens.

## Precio Fundador

- Instalacion privada: 500 EUR.
- Soporte basico: 50 EUR/mes.
- API externa: la paga el doctor directamente a OpenAI, Anthropic/Claude, Gemini u otro proveedor.

## Opciones Que Puedes Ofrecer

### Opcion A: Evidentia Local App

Instalas Evidentia en el ordenador del doctor o del centro.

- El RAG se guarda en ese ordenador, dentro de la carpeta local de Evidentia.
- El doctor abre la app en navegador.
- Si quiere usar movil, el movil accede al nodo local; no guarda el RAG principal.
- Es la opcion mas barata y rapida.

### Opcion B: Evidentia Node Appliance

Le vendes un Mac mini u ordenador dedicado ya preparado.

- El RAG se guarda en el Mac mini.
- El cliente no toca instalaciones tecnicas.
- Puede acceder desde navegador en ordenador, tablet o movil.
- Es la opcion premium y con mas margen.

## Antes De Instalar

Pide al doctor estas respuestas:

1. Donde quiere instalarlo: su ordenador principal, un Mac mini/PC dedicado, servidor interno o NAS.
2. Si quiere usar IA externa o empezar solo con RAG local.
3. Que proveedor de IA quiere usar: OpenAI, Claude, Gemini u otro.
4. Si ya tiene API key. Si solo tiene ChatGPT Plus o Claude web, eso no sirve como API automatica.
5. Que primeros materiales quiere cargar: 3-5 PDFs, protocolos, audios, notas o casos anonimizados.
6. Confirmacion de que no cargara datos identificables de pacientes sin permiso.

## Instalacion Paso A Paso

### 1. Preparar La Carpeta Del Cliente

Crear una carpeta privada para ese doctor:

```bash
mkdir -p ~/Evidentia-Local-Node
```

Copiar ahi el paquete de Evidentia. Para piloto inicial, cada doctor debe tener su propia carpeta/instancia.

### 2. Crear Configuracion Privada

Crear un archivo `.env` dentro de la carpeta de Evidentia:

```bash
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=
```

Si el doctor tiene API key, ponerla ahi. Si no tiene API key, dejarla vacia y arrancar en modo RAG local.

Regla: nunca poner la API key en el navegador, WhatsApp, email sin cifrar ni documentos compartidos.

### 3. Arrancar Evidentia

En macOS, usar el launcher si existe:

```bash
./start_evidentia.command
```

O arrancar manualmente:

```bash
python3 server.py
```

Abrir:

```text
http://127.0.0.1:8892/
```

### 4. Comprobar Salud

Abrir o ejecutar:

```bash
curl -sS http://127.0.0.1:8892/api/health
curl -sS http://127.0.0.1:8892/api/ai/status
```

Resultado esperado:

- `api/health` responde `ok: true`.
- `api/ai/status` dice `OpenAI activo` si hay API key.
- Si no hay API key, debe decir modo local/RAG sin bloquear el uso.

### 5. Cargar Primer Conocimiento

Cargar solo material autorizado o anonimizado:

- 1 protocolo PDF.
- 1 audio corto de criterio del doctor.
- 1 nota de caso anonimizada.
- 1 foto/documento no identificable si aplica.
- 1 lista de decisiones o aprendizajes.

No cargar datos identificables de pacientes en la primera demo si no hay consentimiento claro.

### 6. Probar Preguntas

Hacer 3 preguntas simples:

1. Que protocolos he guardado sobre este tema?
2. Que decisiones o aprendizajes aparecen en mis notas?
3. Que fuentes justifican esta respuesta?

La demo solo vale si la respuesta muestra fuentes o registros recuperados.

### 7. Explicar Limites

Decirlo claro:

> Evidentia no diagnostica ni decide por ti. Ordena tu conocimiento y te ayuda a recuperarlo con fuentes. La decision profesional sigue siendo tuya.

### 8. Backup Basico

Antes de terminar, crear un backup:

```bash
scripts/evidentia_backup_restore.sh backup
```

Explicar al doctor donde queda el backup y acordar frecuencia:

- Manual al inicio.
- Semanal si el piloto avanza.
- Automatizado solo si el cliente paga mantenimiento ampliado.

## Cuando Hace Falta Una Empresa Externa

No hace falta empresa externa si:

- Es un solo ordenador.
- El doctor usara navegador local.
- La API key la pone el cliente.
- No hay integracion con servidor corporativo.

Si hace falta empresa externa o informatico del centro cuando:

- Quieren instalarlo en servidor compartido.
- Quieren acceso desde varios ordenadores de la clinica.
- Hay firewall, VPN, NAS o dominio interno.
- Hay exigencias RGPD/IT formales.
- Quieren backups automaticos cifrados gestionados.

## Opcion Mac Mini Vendible

Si el doctor no quiere instalar nada en su ordenador, ofrecer:

> Te entrego un Mac mini preparado como nodo privado de Evidentia. Lo conectas a la red, abres Evidentia desde el navegador y todo tu conocimiento queda dentro de ese equipo. Si quieres IA externa, se conecta con tu propia API.

Esta opcion permite cobrar:

- Hardware con margen.
- Setup tecnico premium.
- Soporte mensual.
- Backup/mantenimiento ampliado si lo quiere.

Limite: no prometer una oficina IA completa abierta. La primera venta debe ser Evidentia funcionando como memoria privada, no una plataforma de agentes generalista.

## Checklist De Cierre

- Evidentia abre en navegador.
- Se ha probado `api/health`.
- IA externa activa o modo local explicado.
- Se cargaron 3-5 materiales de prueba.
- Una pregunta devuelve fuentes.
- El doctor entiende limites y propiedad de datos.
- Backup creado.
- Precio y soporte aceptados: 500 EUR setup + 50 EUR/mes.
