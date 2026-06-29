# Evidentia - Guion Demo Vendible SEPES

Fecha: 2026-06-25

## Objetivo

Demostrar en 10 minutos que Evidentia no es una landing ni un chat generico: es un nodo local-first para convertir conocimiento disperso en memoria consultable con fuentes.

## Preparacion

1. Confirmar que el nodo local esta vivo:
   ```bash
   curl -sS http://127.0.0.1:8892/api/health
   curl -sS http://127.0.0.1:8892/api/rag/stats
   curl -sS http://127.0.0.1:8892/api/ai/status
   ```
2. Preparar la puerta de microvideo y dejar evidencia reproducible:
   ```bash
   scripts/prepare_sellable_microvideo.sh
   ```
   El comando debe generar un manifiesto en `qa/microvideo/` con health, RAG, chat con fuentes, export y secuencia de grabacion. Si falla, no grabar ni prometer demo vendible.
3. Preparar la puerta comercial del piloto fundador:
   scripts/pilot_readiness_snapshot.sh
   El comando debe generar una ficha en qa/pilot-readiness/ con registros, chunks, fuentes, estado de IA, knowledge bundle y secuencia de cierre. Si falla, no usar la demo para cerrar piloto.
4. Si la base no muestra al menos 3 registros y 3 fragmentos RAG, cargar el seed vendible:
   ```bash
   scripts/seed_sellable_demo.sh
   ```
5. Abrir la web:
   `http://127.0.0.1:8892/website.html#web`
6. Abrir la app:
   `http://127.0.0.1:8892/index.html#intake`
7. Confirmar que aparecen 3 registros demo:
   - `DEMO-EST-001`
   - `DEMO-OPS-002`
   - `DEMO-FORM-003`
8. Hacer backup antes de una demo importante:
   ```bash
   scripts/evidentia_backup_restore.sh backup
   ```

## Puerta De Demo

No empezar una demo comercial si falla cualquiera de estos puntos:

- `/api/health` no responde.
- `/api/rag/stats` muestra 0 fragmentos.
- La app no ensena registros demo despues del seed.
- No puedes decir claramente: "esto no diagnostica ni decide; recupera memoria propia con fuentes".
- scripts/pilot_readiness_snapshot.sh no genera PASS.

Si falla la IA externa, la demo puede continuar solo si el chat responde en modo RAG local con fuentes recuperadas.

## Apertura Verbal

> Evidentia no diagnostica ni decide por nadie. Convierte conocimiento disperso de una persona, equipo o centro en una memoria privada consultable con fuentes. La decision sigue siendo humana.

## Demo De 10 Minutos

1. Web, 60 segundos:
   - Mostrar `Web publica completa`.
   - Ensenar pestanas: Home, Producto, Dental, Confianza, Piloto, Contacto.
   - Mostrar bloque de video.
   - Mostrar oferta `Piloto Fundador Evidentia Local Node`.

2. App, 90 segundos:
   - Abrir `Ingesta`.
   - Mostrar que el nodo local ya contiene los 3 registros demo cargados por seed.
   - Explicar que son datos ficticios y que el piloto real solo usa datos autorizados.

3. Casos, 90 segundos:
   - Abrir `Casos`.
   - Seleccionar `DEMO-EST-001`.
   - Mostrar fuentes: foto polarizada, protocolo, audio de criterio.

4. Mapa/Entidades, 90 segundos:
   - Abrir `Entidades` o `Mapa`.
   - Explicar que el sistema conecta area, material, criterio, resultado y evidencia.

5. Chat, 2 minutos:
   Preguntar:
   - `Que conocimiento conecta estetica, laboratorio y aprendizaje?`
   - `Que criterios repetimos en los casos esteticos?`
   - `Donde faltan fuentes antes de convertirlo en protocolo?`

   Respuesta vendible esperada: debe citar registros/fuentes recuperadas. Si responde sin fuente, no usar esa respuesta como prueba.

6. Intel, 90 segundos:
   - Mostrar busquedas evitadas, riesgos, contradicciones y memoria de expertos.
   - Explicar que esas son senales de valor, no claims clinicos.

7. Pack, 60 segundos:
   - Abrir `Pack`.
   - Exportar pack del caso.
   - Cerrar con trazabilidad: fuentes, relaciones y limites.

8. Conectar, 60 segundos:
   - Abrir `Conectar`.
   - Descargar `knowledge bundle`.
   - Explicar que el mirror puede entregarse a un agente, project o automatizacion con politica de uso y fuentes, sin convertir Evidentia en software medico.

## Oferta Que Se Puede Decir Sin Disculparse

**Piloto Fundador Evidentia Local Node**

- Duracion: 30 dias.
- Setup fundador: 500 EUR por instalacion privada.
- Incluye instalacion local, carga inicial guiada, preguntas reales, demo privada, memory report y roadmap de 30 dias.
- Continuidad fundador: 50 EUR/mes por mantenimiento basico, soporte y actualizaciones ligeras.
- Costes de IA externa: los paga y controla el cliente con su propia API/proveedor.

## Criterios De Exito Del Piloto

- Recupera decisiones que antes costaba encontrar.
- Conecta fuentes dispersas.
- Detecta huecos antes de cerrar un protocolo.
- Reduce dependencia de una sola persona experta.
- Genera un pack revisable con fuentes.

## Limites Obligatorios

- No es software medico.
- No diagnostica.
- No sustituye criterio profesional.
- No usa datos sensibles sin permiso.
- No promete resultados clinicos.

## Cierre Comercial

> Si en 30 dias el mirror no recupera fuentes utiles ni reduce busqueda real, paramos. Si recupera contexto, detecta huecos y prepara mejores decisiones humanas, entonces sabemos que conocimiento merece convertirse en sistema.

## Fallback Comercial Seguro

Si algo falla durante la demo:

- No improvisar capacidades clinicas.
- Decir: "esto es precisamente lo que medimos en piloto: que el nodo local, las fuentes y el backup sean repetibles".
- Enseñar la web, el one-pager y el backup/seed como prueba de construccion real.
- Reagendar demo tecnica solo cuando `/api/health`, `/api/rag/stats` y chat con fuentes pasen.
