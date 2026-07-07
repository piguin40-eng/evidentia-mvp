# Evidentia - One-Pager Piloto Fundador

Fecha: 2026-06-23

## Frase Corta

Evidentia Local Node instala una memoria IA privada en el entorno del cliente: sus datos, su conocimiento y su proveedor de IA, pagado y controlado por el propio doctor o centro.

## Que Es

Evidentia es un Vector Knowledge Mirror local-first: un nodo local que guarda, estructura, indexa y permite consultar el conocimiento propio del cliente.

La version vendible inmediata no es una plataforma multi-tenant compleja. Es una instalacion privada por cliente:

- Base de datos local del cliente.
- Archivos y uploads locales del cliente.
- Base vectorial local del cliente.
- Clave/API de IA del cliente, si quiere sintesis externa.
- Miguel/Helix no paga los tokens del cliente y no retiene sus datos.

Dental es el primer vertical de piloto porque el dolor de perdida de contexto es claro, pero la promesa no es clinica: es memoria contextual, trazabilidad y recuperacion de conocimiento.

## Que Problema Resuelve

- El conocimiento valioso queda disperso en WhatsApp, carpetas, audios, fotos, PDF, notas y memoria personal.
- El equipo repite busquedas, pierde decisiones pasadas y depende demasiado de personas clave.
- Las fuentes existen, pero no estan conectadas ni son consultables en el momento de decidir.

## Que Incluye El Piloto

- Instalacion local de Evidentia Local Node.
- App en navegador sobre datos locales.
- SQLite local para registros.
- Indice vectorial compacto local para busqueda semantica/RAG, con espejo SQLite de chunks y fuentes.
- Configuracion opcional de la IA propia del cliente: OpenAI, Claude, Gemini, proveedor compatible o modo RAG local sin IA externa.
- Upload real de archivos.
- Ingesta de texto, PDF/TXT/MD/CSV/JSON/HTML, imagen, audio y video propio o autorizado.
- Transcripcion local de audio/video cuando existan ffmpeg y Whisper CLI.
- Chat con fuentes sobre el conocimiento indexado.
- Busqueda local y mapa de conocimiento.
- Documento de consentimiento y limites.
- Sesion de carga inicial y demo guiada.
- Criterios de aceptacion y no-go definidos antes de cargar datos: ver `FOUNDER_PILOT_ACCEPTANCE.md`.

## Que No Es

- No es software medico validado.
- No diagnostica.
- No sustituye criterio profesional.
- No promete tratamiento, resultado clinico ni decision automatica.
- No usa datos sensibles sin permiso, minimizacion y supervision humana.

## Comprador Ideal

Profesional, clinica, laboratorio, centro, formador o equipo experto que ya genera conocimiento valioso y quiere dejar de perderlo entre archivos, conversaciones y memoria humana.

## Prueba De Valor En 7 Dias

El piloto debe demostrar al menos una de estas senales:

- Recuperar una decision, protocolo o aprendizaje que antes costaba encontrar.
- Conectar fuentes dispersas de un caso, proyecto o tema.
- Reducir dependencia de una sola persona para explicar criterio acumulado.
- Crear una base reutilizable de conocimiento propio con fuentes visibles.

## Entregables En 30 Dias

- Nodo local funcionando con datos ficticios, anonimizados o autorizados.
- Preguntas reales probadas contra el conocimiento indexado.
- Respuestas con fuentes visibles y revisables.
- Export knowledge bundle o pack del conocimiento cargado.
- Backup creado y restauracion verificada sin tocar datos activos.
- Memory report final: valor encontrado, huecos, riesgos y decision de continuidad.

## Oferta Recomendada

Nombre: Piloto Fundador Evidentia Local Node.

Duracion: 30 dias.

Setup fundador inicial: 500 EUR por instalacion privada.

Continuidad fundador inicial: 50 EUR/mes por mantenimiento basico, soporte y actualizaciones ligeras. Los costes de API/IA externa los paga el cliente directamente a su proveedor.

Nota interna: este precio es de entrada para cerrar validacion y primeros doctores. No debe venderse como tarifa definitiva si el soporte, backups, migraciones o carga inicial crecen.

## Dos Opciones Comerciales

### 1. Evidentia Local App

Instalacion de la app en el ordenador del doctor o centro.

- El RAG vive dentro de la carpeta local de Evidentia, en el mismo equipo donde corre el backend.
- La app web se abre desde navegador.
- El movil puede usarse como acceso si el equipo local esta encendido y compartido en la red, pero el RAG no debe depender del movil en v0.
- Precio fundador: 500 EUR setup + 50 EUR/mes soporte basico.

### 2. Evidentia Node Appliance

Mac mini u ordenador dedicado preparado por Helix.

- El RAG vive dentro del Mac mini/appliance.
- Evidentia ya va preinstalado.
- El cliente accede desde navegador en ordenador, tablet o movil de la red.
- Opcion mas limpia para clinicas que no quieren tocar instalaciones.
- Permite margen de hardware + setup premium + soporte mensual.

## Opcion Premium: Evidentia Node Appliance

Para clientes que no quieren tocar instalaciones, se puede vender un Mac mini preparado como nodo privado:

- Mac mini configurado y entregado por Helix.
- Evidentia Local Node preinstalado.
- Carpeta de datos, backups y arranque ya preparados.
- Acceso por navegador desde la clinica/laboratorio.
- IA externa conectada solo con API del cliente.
- Margen comercial sobre hardware + setup tecnico.

Regla critica: no vender OpenClaw Office completo como asistente abierto del cliente en v0. Vender un appliance cerrado de Evidentia. Cualquier capa tipo oficina/agentes debe estar limitada, auditada y separada de los datos/persona de Miguel.

Condicion comercial: precio fundador a cambio de feedback semanal, permiso para usar aprendizajes anonimizados y una decision clara al final del piloto.

## Objeciones Y Respuesta Corta

### "Esto es IA medica?"

No. Es memoria privada consultable con fuentes. La decision sigue siendo humana.

### "Mis datos salen fuera?"

La base del piloto es local-first. Los datos y archivos quedan en el entorno del cliente. Si el cliente activa IA externa, se usa su propia API/proveedor y debe autorizarlo expresamente.

### "Tengo que darte mi cuenta de IA?"

No. La cuenta y la API son del cliente. Evidentia solo se configura para conectarse a esa IA desde su propio nodo. Si no tiene API, el nodo funciona en modo RAG local hasta que la contrate.

### "Que pasa si falla?"

El piloto se mide como herramienta de organizacion y recuperacion de conocimiento, no como sistema critico. Se mantiene backup local y se documentan limites.

### "Por que pagar ahora si esta en piloto?"

Porque el valor no es comprar software terminado: es construir una memoria propia desde el primer dia con instalacion, carga inicial, soporte y adaptacion al caso real.

## Proxima Accion Comercial

Elegir dos candidatos, completar PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md, pasar MICRODEMO_ACCEPTANCE_GATE.md, pedir una microdemo de 10 minutos con aprobacion explicita de Miguel, instalar dos nodos separados, cargar 3-5 registros ficticios o anonimizados por candidato, activar su IA solo si tienen API propia, ejecutar la demo y cerrar prueba pagada con mantenimiento mensual.

## Cierre Seguro

Evidentia no promete saber mas que el experto. Promete que el experto y su equipo pierdan menos conocimiento, recuperen mejor sus fuentes y decidan con mas contexto.
