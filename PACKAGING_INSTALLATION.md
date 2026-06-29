# Evidentia - Packaging e instalacion cliente

Fecha: 2026-06-18

## Posicionamiento cerrado

Evidentia no se vende como plataforma de diagnostico. Se vende como plataforma para guardar, organizar y consultar el conocimiento propio del cliente.

El conocimiento que entra en Evidentia pertenece al cliente. Evidentia no se apropia de ese conocimiento, no lo reutiliza para otros clientes y no promete diagnostico clinico.

Frase base:

> Evidentia instala una base de conocimiento privada en el ordenador o servidor del cliente para que pueda guardar sus datos, documentos, fotos, videos, protocolos, errores, decisiones y aprendizajes, y consultarlos despues con fuentes.

## Valor real

- Guardar conocimiento que ahora esta disperso.
- Consultar el propio historial y criterio del equipo.
- Aprender de errores o incidencias pasadas sin depender de memoria humana.
- Encontrar casos, protocolos, decisiones y evidencias similares.
- Convertir datos propios en una base consultable.
- Mantener el control local del conocimiento.

## Que no promete

- No diagnostica pacientes.
- No sustituye criterio clinico.
- No promete tratamiento correcto.
- No es producto sanitario validado.
- No aprende de otros clientes sin permiso.
- No envia datos sensibles a terceros por defecto.

## Modelo de entrega

### Opcion recomendada v0.1

Paquete instalable local:

- Carpeta/app Evidentia Local Node.
- Launcher para arrancar servidor local.
- Base SQLite local.
- Chroma local para RAG.
- Carpeta de uploads local.
- Carpeta de exports local.
- Backup manual simple.
- Guia de instalacion.
- Guia de uso inicial.

El cliente accede desde navegador en su propio ordenador o red local.

### Donde Vive El RAG

En v0, el RAG vive siempre en el nodo donde estan los datos:

- Si vendemos solo la app local, el RAG vive dentro de la carpeta de Evidentia en el ordenador del cliente: `data/rag/`.
- Si vendemos Mac mini appliance, el RAG vive dentro del Mac mini.
- El movil no es el sitio principal para el RAG. El movil puede abrir la app por navegador contra el nodo local, pero la base vectorial debe estar en ordenador/servidor/appliance.

Regla comercial: explicar que Evidentia no es una app movil aislada; es una memoria privada instalada en un nodo del cliente. El movil es una pantalla de acceso, no el cerebro del sistema.

### Opcion premium v0.2: Mac mini appliance

Para clientes con poca capacidad tecnica, se puede vender un Mac mini ya preparado:

- Evidentia Local Node preinstalado.
- Datos y base vectorial dentro del Mac mini del cliente.
- Arranque con doble clic o servicio local.
- Backup basico configurado.
- API externa del cliente, no de Helix.
- Margen de hardware + setup.

No instalar un OpenClaw Office completo abierto en cliente sin hardening. Si se usa una capa visual/oficina, debe ser una version cerrada y limitada a Evidentia, sin memoria privada de Miguel, sin credenciales de Helix y sin acceso a herramientas no necesarias.

### Como se entrega

1. Se envia paquete comprimido o instalador.
2. Se ejecuta instalacion asistida.
3. Se crea carpeta local del cliente.
4. Se abre Evidentia en navegador.
5. Se carga conocimiento inicial.
6. Se prueba busqueda/chat/fuentes.
7. Se explica backup y limites.

## Oferta comercial inicial

Nombre: Piloto Fundador Evidentia Local Node.

Incluye:

- Instalacion local.
- Configuracion inicial.
- Carga guiada de conocimiento.
- Formacion breve.
- Soporte piloto.
- Revision de uso.
- Documento de limites y privacidad.

Precio fundador inicial:

- Setup: 500 EUR por instalacion privada.
- Continuidad: 50 EUR/mes por soporte basico, mantenimiento y actualizaciones ligeras.
- La API/IA externa la paga el cliente directamente a su proveedor.

Nota interna: este precio es para cerrar validacion con los primeros doctores. No debe convertirse en tarifa definitiva si el soporte, backups, migraciones, carga inicial o personalizacion crecen.

## Mensaje comercial simple

"No te vendo una IA que diagnostica. Te vendo una memoria privada para que tu clinica o laboratorio no pierda su conocimiento. Todo lo que guardas sigue siendo tuyo, queda en tu entorno, y puedes consultarlo despues con fuentes."

## Requisito tecnico antes de venderlo

Antes de venderlo en SEPES, el paquete debe instalarse en un ordenador externo sin depender del entorno de desarrollo de piguin.

Checklist minimo:

- Arranque con doble clic o comando claro.
- Verificacion de dependencias.
- Mensajes claros si falta ffmpeg, Python, Chroma o permisos.
- Modo demo.
- Modo cliente limpio.
- Backup/restauracion.
- Guia PDF o Markdown.
- Prueba completa post-instalacion.
