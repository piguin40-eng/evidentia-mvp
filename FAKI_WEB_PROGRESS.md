# FAKI WEB PROGRESS - EVIDENTIA

## 2026-07-07 - Executive spine comercial y QA visual

### Avances de hoy

- Añadi una nueva seccion `Executive spine` justo despues de la prueba operativa para que el comprador entienda antes del scroll profundo: tesis, prueba, frontera humana y compra.
- Converti el bloque en un tablero 2x2 legible: `Vector Knowledge Mirror`, `10 preguntas contra fuentes reales`, `No diagnostica. No decide.` y `Build, adjust or stop`.
- Anadi una banda de senales de conversion: input minimo, test real, output y CTA directo al entregable.
- Suavice la opacidad del video en mobile para que el texto fantasma del hero no compita tanto con el titular.
- Corregi un fallo de visibilidad con anchors: el bloque nuevo ya no depende del `IntersectionObserver` para aparecer cuando se entra por `#spine`.
- Ajuste desktop de la seccion de 4 columnas a 2x2 para eliminar truncados y subir legibilidad premium.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v83-executive-spine.png`
  - `qa/evidentia-landing-mobile-v83-executive-spine.png`
  - `qa/evidentia-landing-mobile-v84-hero-dimmed-video.png`
  - `qa/evidentia-landing-desktop-v88-spine-2x2.png`
  - `qa/evidentia-landing-mobile-v88-spine-2x2.png`

### Referencias usadas

- Linear: producto y mecanismo visibles antes de explicar demasiado.
- Rive: motion/linea de senal como estado de proceso, no decoracion gratuita.
- Notion AI / WorkOS: confianza, permisos y frontera humana como argumento de compra.
- Vertical AI interno: negro profundo, gradiente iridiscente y display fuerte, pero aplicado a infraestructura sensible.

### Decisiones de diseno

- No anadi otra promesa larga. Anadi una columna ejecutiva para ordenar lo que ya existe y reducir confusion en una pagina muy extensa.
- El bloque nuevo usa lenguaje de decision comercial: que es, como se prueba, que no promete y que se compra.
- Mantengo dental fuera del primer argumento del bloque: dental sigue como primer vertical, no como definicion del producto.
- Use 2x2 en desktop porque cuatro cards en una fila daban clipping y parecian menos premium.

### Riesgos

- La pagina sigue demasiado larga; necesita una pasada editorial para fusionar bloques redundantes antes de review final de Miguel.
- Queda pendiente el microvideo real completo de app local: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- Hay deuda CSS acumulada con overrides mobile y anchors; hoy se corrigio el bloque nuevo, no se hizo refactor global.
- Hay copy sin acentos en el bloque nuevo por consistencia tecnica rapida; conviene una pasada final de microcopy.

### Verificacion

- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Servidor local usado: `http://127.0.0.1:8899/website.html?v=20260707-executive-spine5`.
- Capturas con Chrome del sistema via Playwright CLI:
  - Desktop spine: `qa/evidentia-landing-desktop-v88-spine-2x2.png`.
  - Mobile spine: `qa/evidentia-landing-mobile-v88-spine-2x2.png`.
  - Mobile hero suavizado: `qa/evidentia-landing-mobile-v84-hero-dimmed-video.png`.
- Vision QA final: sin texto truncado ni solape grave en `Executive spine`; el bloque es presentable como avance.

### Siguiente paso

1. Pasada editorial global: reducir secciones duplicadas y dejar una narrativa de publicacion mas corta.
2. Producir microvideo real de app local con el loop completo del piloto.
3. Revisar acentos y consistencia de idioma en copy final.
4. QA full-page por tramos desktop/mobile despues del recorte.

### Estado

NO LISTA PUBLICA FINAL - El avance de hoy mejora mucho la lectura comercial temprana y el hero mobile, pero no marco `READY_FOR_MIGUEL_REVIEW` hasta cerrar recorte editorial y microvideo real.

## 2026-07-06 - Mobile hero publication pass y QA CDP

### Avances de hoy

- Hice una pasada quirurgica sobre el primer viewport movil: el mensaje ya no parece otra landing distinta al desktop.
- Reescribi el hero mobile hacia la tesis grande: "Tu conocimiento ya existe. EVIDENTIA lo convierte en memoria."
- Converti el CTA movil \`Abrir app local\` en un dock fijo visible, con safe-area y sin depender del scroll inicial.
- Compacte el hero movil para eliminar la sensacion de vacio negro bajo el mini mirror.
- Añadi un override final de publicacion para contener ancho global sin tocar las secciones ya verificadas.
- Actualice el cache-buster CSS a \`20260706-mobile-hero-publication-pass\`.

### Archivos tocados

- \`website.html\`
- \`website.css\`
- \`FAKI_WEB_PROGRESS.md\`
- Capturas QA generadas:
  - \`qa/evidentia-landing-desktop-v59-mobile-hero-publication-pass.png\`
  - \`qa/evidentia-landing-mobile-v59-mobile-hero-publication-pass.png\`
  - \`qa/evidentia-landing-mobile-v60-mobile-hero-final.png\`
  - Comparacion previa: \`qa/evidentia-landing-desktop-v58-preflight-20260706-cdp.png\`, \`qa/evidentia-landing-mobile-v58-preflight-20260706-cdp.png\`

### Referencias usadas

- Linear: mantener producto vivo y primer viewport con sistema visible.
- Granola / Mem: memoria privada explicada como recuperacion contextual, no captura infinita.
- Notion AI / WorkOS pattern: control, permisos y gobernanza como argumento de confianza.
- Rive: motion y fondo visual como lectura de sistema, sin competir con el copy mobile.

### Decisiones de diseno

- No añadi otra seccion: la web ya tiene 27 bloques y mas de 33.000 px de alto en desktop; el avance de calidad era pulir el punto de entrada y reducir friccion mobile.
- Mobile queda alineado con el posicionamiento principal: Vector Knowledge Mirror local-first, fuentes, relaciones y revision humana.
- El CTA fijo en mobile prioriza conversion y acceso a app local sin romper privacidad ni publicar nada externo.
- Mantengo dental como primer vertical en secciones posteriores, no en el hero principal.

### Riesgos

- La pagina sigue siendo larga y necesita una pasada editorial para fusionar o recortar bloques redundantes antes de publicacion final.
- Sigue pendiente el microvideo real completo: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- \`body.scrollWidth\` en desktop sigue midiendo 1491 con viewport 1440 aunque CDP no detecta elementos normales fuera de pantalla; parece venir de una capa fija/pseudo visual y requiere limpieza CSS mas estructural.
- El CSS conserva deuda acumulada de overrides mobile; la solucion de hoy es segura y acotada, no una refactorizacion.

### Verificacion

- Servidor local usado: \`http://127.0.0.1:8899/website.html?v=20260706-mobile-hero-publication-pass2\`.
- \`HTMLParser\` OK para \`website.html\`.
- Sintaxis JS inline OK con \`new Function(script)\`.
- Braces CSS OK.
- Chrome/CDP genero capturas desktop/mobile y midio overflow:
  - Desktop: viewport 1440, \`docW 1440\`, sin offenders ni errores de consola.
  - Mobile: viewport 390, \`bodyW 390\`, \`docW 390\`, hero 774 px, CTA fijo visible, sin offenders ni errores.
- Vision QA final: mobile aceptable, premium, legible, CTA claro, sin vacios problematicos ni solapes criticos.

### Siguiente paso

1. Grabar o montar microvideo real de app local completa.
2. Hacer limpieza editorial: reducir 27 secciones a una narrativa mas afilada y publicable.
3. Resolver el \`body.scrollWidth\` desktop con refactor CSS de capas fijas/pseudo-elementos.
4. QA full-page desktop/mobile con capturas por tramos, no solo primer viewport.

### Estado

NO LISTA PUBLICA FINAL - El primer viewport mobile ya esta mucho mas cerca de nivel publicable, pero no marco \`READY_FOR_MIGUEL_REVIEW\` hasta cerrar microvideo real, limpieza editorial y QA completa de pagina.

## 2026-07-05 - Language trust pass y cierre de piloto accionable

### Avances de hoy

- Hice una pasada de direccion sobre el primer viewport: lenguaje mas consistente en espanol, menos mezcla ES/EN y copy del hero mas limpio.
- Cambie el mensaje de API externa a una formulacion mas defendible: API de IA elegida y controlada por el cliente.
- Añadi un bloque `pilot-prep` dentro del CTA final para convertir el cierre en una accion clara: 50-200 piezas, 10 preguntas reales y 1 criterio de compra.
- Ajuste el hero para dar mas aire al proof rail desktop y reducir riesgo de colision con la tarjeta lateral en escritorios estrechos.
- Suavice el video de fondo en mobile para que no compita con el copy.
- Actualice el cache-buster CSS a `20260705-language-trust-pass`.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v57-language-trust-final.png`
  - `qa/evidentia-landing-mobile-v99-language-trust-final.png`
  - Capturas previas de comparacion: `v55-v56` desktop y `v97-v98` mobile.

### Referencias usadas

- Linear: producto vivo y hero con interfaz protagonista.
- Notion AI / WorkOS pattern: confianza desde permisos, control y gobernanza, no desde promesa generica.
- Granola / Mem: memoria privada convertida en recuperacion contextual, evitando sensacion de captura total.
- Rive: motion como lectura de sistema, reduciendo decoracion que compite con el mensaje.

### Decisiones de diseno

- Mantengo EVIDENTIA como infraestructura de memoria local-first, no como producto clinico ni dental-only.
- El cierre final ya no solo invita a abrir app: explica exactamente que debe preparar un comprador para una prueba seria.
- El copy del hero debe vender control y criterio recuperable antes que tecnologia por tecnologia.
- La version mobile prioriza legibilidad sobre show visual: el video baja intensidad para dejar respirar titulo, CTA y mini mirror.

### Riesgos

- La pagina sigue siendo larga y con deuda CSS acumulada de overrides mobile; conviene una limpieza estructural antes de publicacion final.
- Falta todavia el microvideo real completo de app local: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- El hero desktop es potente pero denso; en la siguiente pasada conviene evaluar si se recorta un poco el peso tipografico sin perder impacto.
- No pude hacer una medicion automatica de overflow via Playwright API porque el modulo `playwright` no esta disponible para `require()`; si pude generar capturas con Playwright CLI usando Chrome del sistema.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8899/website.html?v=20260705-language-trust-pass-final`.
- `HTMLParser` OK para `website.html`.
- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Playwright CLI con `--channel=chrome` genero capturas desktop/mobile.
- Vision QA final:
  - Desktop: sin clipping severo, solapes graves, media rota ni texto ilegible visible.
  - Mobile: legible, sin overflow visual evidente; el video de fondo ya no bloquea lectura.

### Siguiente paso

1. Grabar o montar microvideo real de app local completa: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
2. Limpiar CSS mobile acumulado y resolver medicion de overflow global con herramienta programatica estable.
3. Hacer pasada editorial de ritmo para fusionar secciones redundantes y dejar una narrativa mas afilada.
4. Preparar QA de pagina completa desktop/mobile, no solo primer viewport y bloques aislados.

### Estado

NO LISTA PUBLICA FINAL - La web mejora en confianza, lenguaje y accion comercial, pero no marco `READY_FOR_MIGUEL_REVIEW` hasta cerrar microvideo real, limpieza CSS/mobile y QA completa de pagina.

## 2026-07-04 - Pilot deliverable y cierre comprable del piloto

### Avances de hoy

- Añadi una nueva seccion `pilot-deliverable` con ancla `#entregable`.
- La seccion convierte el final del piloto en un entregable concreto: `Memory Report / Decision Pack`.
- El bloque muestra una decision `Build`, evidencia, gaps, ROI operativo y siguiente alcance a 30 dias.
- Actualice la navegacion superior con acceso directo a `Entregable`.
- Actualice el cache-buster CSS a `20260704-pilot-deliverable`.
- Añadi un fallback CSS especifico para que la seccion no quede invisible si falla el `IntersectionObserver` de `.reveal`.
- Centre el bloque en desktop con ancho maximo `1220px` para evitar el clipping del titular detectado en QA.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v54-pilot-deliverable-final.png`
  - `qa/evidentia-landing-mobile-v96-pilot-deliverable-final.png`
  - Capturas intermedias de debug: `v48-v53` desktop y `v90-v95` mobile.

### Referencias usadas

- Linear: producto vivo y estado de decision visible, no claim abstracto.
- Stripe / WorkOS pattern: infraestructura sensible vendida desde control, alcance y confianza.
- Claude Code: salida gobernada por revision humana, limites y siguiente accion verificable.
- Rive: motion/señal como explicacion de progreso, no decoracion.

### Decisiones de diseno

- El bloque responde a una objecion comercial concreta: que compra el cliente al final del piloto.
- La salida no es "demo bonita"; es un paquete de decision con evidencia, gaps, ROI y siguiente scope.
- Mantengo copy sin claims clinicos ni promesa de diagnostico: EVIDENTIA prepara contexto y trazabilidad, el humano decide.
- El visual usa un report panel premium para que la venta se sienta tangible y no una plataforma infinita.

### Riesgos

- Sigue pendiente el microvideo real de app local completa: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- Chrome/CDP detecta overflow horizontal global en desktop (`bodyW 1491` con viewport `1440`), pero la nueva seccion queda centrada y no parece ser la causa.
- El CSS tiene deuda acumulada de overrides mobile y reglas repetidas; conviene limpieza antes de publicacion final.
- La web ya tiene muchas secciones potentes; falta una pasada editorial para recortar redundancia y subir ritmo.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8898/website.html?v=20260704-pilot-deliverable-fix2`.
- `HTMLParser` OK para `website.html`.
- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Chrome headless/CDP genero capturas desktop/mobile de la seccion con scroll real.
- Vision QA final:
  - Desktop: visible, legible, premium, sin clipping/overlap obvio en la seccion.
  - Mobile: stack limpio, legible, sin overflow horizontal visible.

### Siguiente paso

1. Grabar o montar microvideo real del flujo local completo y conectarlo con `pilot-film` / `director-cut`.
2. Limpiar overflow horizontal global y CSS mobile acumulado.
3. Recortar o fusionar secciones redundantes para que la pagina tenga ritmo de venta final.
4. Hacer QA final de pagina completa desktop/mobile, no solo bloque por bloque.

### Estado

NO LISTA PUBLICA FINAL - La nueva seccion `#entregable` ya queda lista como pieza de conversion, pero no marco `READY_FOR_MIGUEL_REVIEW` hasta cerrar microvideo real, overflow global y limpieza editorial.

## 2026-07-03 - Pilot film interactivo y cierre de storytelling comprable

### Avances de hoy

- Añadi una nueva seccion `pilot-film` justo despues del bloque de video principal.
- La seccion convierte el microvideo pendiente en una experiencia interactiva dentro de la web: `Intake -> Mirror -> Evidence -> Close`.
- Integra video local existente como superficie cinematografica, HUD de señales, tabs por capitulo, script comercial y verdict de conversion.
- Reforce el mensaje clave: EVIDENTIA no pide creer en una IA abstracta; propone probar una memoria propia contra 10 preguntas reales.
- Ajuste responsive mobile del nuevo bloque para evitar overflow y mejorar ancho de copy.
- Actualice cache-buster CSS a `20260703-pilot-film`.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v47-pilot-film-cdp.png`
  - `qa/evidentia-landing-mobile-v89-pilot-film-cdp.png`
  - Capturas auxiliares: `qa/evidentia-landing-desktop-v45-pilot-film-fulltop.png`, `qa/evidentia-landing-mobile-v87-pilot-film-fulltop.png`, `qa/evidentia-landing-desktop-v46-pilot-film-long.png`, `qa/evidentia-landing-mobile-v88-pilot-film-long.png`

### Referencias usadas

- Linear: producto vivo y estado visible en vez de claim generico.
- Rive: motion como explicacion de proceso, no decoracion.
- Pearl / Nabla: confianza en contexto sensible con limites y revision humana.
- Claude Code: trabajo guiado por permisos, verificacion y salida revisable.

### Decisiones de diseno

- El nuevo bloque no sustituye al microvideo real final, pero cubre el hueco comercial actual con una pieza digna y usable.
- La narrativa queda orientada a compra: que ve el comprador, que prueba aparece en pantalla y cual es el CTA natural en cada fase.
- Mantengo dental como primer territorio vendible sin encerrar el producto: el bloque habla de memoria privada, fuentes, RAG, grafo y decision humana.
- Use assets locales ya existentes para no depender de produccion externa ni publicar nada fuera.

### Riesgos

- Sigue pendiente grabar el microvideo real de la app local completa: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- El CSS mobile sigue acumulando deuda historica de overrides; el nuevo bloque queda contenido, pero conviene limpieza estructural antes de publicar.
- Las capturas por URL con fragmento `#pilot-film` salieron negras en Chrome headless; use CDP con scroll al nodo para capturas fiables del bloque.

### Verificacion

- `HTMLParser` OK para `website.html`.
- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Servidores locales temporales usados en `127.0.0.1:8796-8802`.
- Chrome headless genero capturas generales y capturas CDP especificas del bloque.
- Vision QA desktop del bloque: visible, legible, media no blank, sin overlap/clipping/overflow horizontal obvio.
- Vision QA mobile del bloque: mayormente legible, sin overlap ni overflow horizontal obvio; ajuste posterior aplicado para ensanchar copy movil.

### Siguiente paso

1. Grabar microvideo real con flujo de app local y sustituir/reforzar el `pilot-film`.
2. Limpiar CSS mobile acumulado para reducir overrides duplicados antes de publicacion.
3. Hacer una pasada editorial de ritmo: recortar secciones redundantes y dejar una narrativa mas afilada.
4. Preparar build/publicacion con assets de video optimizados y QA desktop/mobile final.

### Estado

NO LISTA PUBLICA FINAL - Hoy la web gana una pieza fuerte de storytelling y conversion, pero no marco `READY_FOR_MIGUEL_REVIEW` hasta integrar microvideo real o cerrar limpieza CSS/mobile.


## 2026-07-02 - Operating contract y confianza comprable

### Avances de hoy

- Añadi una nueva seccion `operating-contract` despues del `trace-ledger`.
- La seccion convierte la tesis premium en contrato operativo: vault con origen, RAG con camino visible, gate humano y cierre de piloto `build / adjust / stop`.
- Refuerza que EVIDENTIA no es producto clinico ni dental-only: es memoria contextual privada para conocimiento sensible con dental como primer vertical natural.
- Actualice el cache-buster CSS a `20260702-operating-contract`.
- Ajuste un detalle mobile del mini mirror para que la linea decorativa quede contenida.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v43-operating-contract.png`
  - `qa/evidentia-landing-mobile-v84-operating-contract.png`
  - `qa/evidentia-landing-mobile-v85-operating-contract-linefix.png`

### Referencias usadas

- Linear: producto vivo explicado con estados y sistema operativo visible.
- Claude Code: autonomia gobernada por permisos, verificacion y revision humana.
- Stripe / WorkOS pattern: infraestructura sensible explicada desde control, limites y confianza.
- Rive: motion funcional como lectura de estado, no show decorativo.

### Decisiones de diseno

- La web necesitaba una capa de gobierno entre `trace-ledger` y `pilot signal`: ahora el comprador entiende no solo que hay fuentes, sino como se controla el uso de esa memoria.
- El copy evita prometer diagnostico, precision clinica o autonomia total. La promesa defendible es memoria privada, recuperacion trazable y decision humana preparada.
- Mantengo el sistema dark premium existente y sumo un tablero operativo con scan sutil para no romper la direccion visual ya aprobada.
- Mobile queda priorizado por legibilidad y contencion: tarjetas en una columna, rail convertido a grid y lineas decorativas ajustadas.

### Riesgos

- Sigue pendiente grabar/integrar el microvideo real del flujo local completo: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.
- El CSS mobile conserva deuda historica de overrides acumulados; funciona en el gate actual, pero hay que limpiarlo antes de publicar fuera.
- La captura desktop muestra mucho aire bajo el hero en viewport alto; no rompe, pero conviene una pasada editorial de ritmo para la version final.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8794/website.html?v=20260702-operating-contract`.
- `HTMLParser` OK para `website.html`.
- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Chrome headless genero capturas desktop/mobile.
- Vision QA:
  - Desktop: sin media rota, clipping, solapamiento ni overflow evidente; detecta aire visual bajo hero.
  - Mobile final: sin clipping/overlap severo, CTA claro y sin bloquear contenido.
- Playwright no disponible en el repo: `Cannot find module 'playwright'`.

### Siguiente paso

1. Grabar o montar microvideo real de app local con guion `Intake -> Mirror -> Proof -> Close`.
2. Hacer limpieza estructural de CSS mobile y retirar overrides duplicados.
3. Recortar ritmo editorial de la pagina larga para que cada bloque empuje venta, no acumulacion.
4. Preparar version publica con assets de video optimizados y prueba final desktop/mobile.

### Estado

NO LISTA PUBLICA FINAL - Hoy sube la confianza y la conversion con una pieza nueva importante, pero no marco `READY_FOR_MIGUEL_REVIEW` hasta integrar microvideo real o cerrar limpieza mobile/CSS.

## 2026-07-01 - Evidence cockpit y hero mobile seguro

### Avances de hoy

- Añadi una nueva seccion `evidence-cockpit` entre prueba visual y `product-loop`.
- La seccion convierte la promesa de EVIDENTIA en una escena de decision: pregunta, fuentes fuertes, fuente contextual, hueco detectado, frontera de privacidad y verdict revisable.
- Cree tres escenarios interactivos: `Experto`, `Equipo` y `Dental`, para reforzar que dental es primer vertical, no limite del producto.
- Actualice el JS inline con `cockpitSteps` y tabs accesibles para cambiar copy, fuentes, confianza y salida.
- Ajuste el hero mobile: retire el CTA movil duplicado, recupere chips/mini mirror compactos y parti el H1 mobile en lineas seguras para evitar clipping.
- Actualice el cache-buster CSS a `20260701-evidence-cockpit`.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v42-full-after-cockpit.png`
  - `qa/evidentia-landing-mobile-v83-hero-title-three-line.png`
  - Intermedias de QA: `qa/evidentia-landing-desktop-v41-evidence-cockpit.png`, `qa/evidentia-landing-mobile-v70-evidence-cockpit.png` hasta `v82`.

### Referencias usadas

- Linear: producto vivo, estados visibles y cockpit de decision.
- Claude Code: autonomia con permisos, verificacion y revision humana.
- Pearl / Nabla: confianza en contextos sensibles sin vender diagnostico ni precision no validada.
- Rive: motion de estado y mapa como explicacion, no decoracion.

### Decisiones de diseno

- La nueva seccion no vende "IA que decide"; vende evidencia defendible antes de decidir.
- El escenario dental habla de fotos, receta, laboratorio, consentimiento y docencia como primer vertical vendible.
- En mobile, priorice legibilidad y ausencia de clipping sobre headline gigante. El H1 queda partido manualmente porque el display condensado no toleraba la frase completa en 390px.
- Mantengo stack estatico HTML/CSS/JS: sigue siendo suficiente para una landing premium mientras no se cree un sistema de animacion mas grande.

### Riesgos

- El CSS mobile acumula muchas capas historicas de overrides; hoy se corrigio el fallo visible, pero conviene una limpieza estructural antes de publicar.
- Chrome headless con fragmentos `#evidence-cockpit` produjo capturas oscuras/no fiables; use captura completa y revision visual de viewport mobile como gate principal.
- Playwright CLI no pudo capturar porque falta el browser instalado en cache; use Google Chrome del sistema.
- Sigue pendiente el microvideo real del flujo local completo: ingesta -> indexacion -> grafo -> pregunta -> fuentes -> decision pack.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8794/website.html`.
- `HTMLParser` OK para `website.html`.
- Sintaxis JS inline OK con `new Function(script)`.
- Braces CSS OK.
- Captura desktop generada: `qa/evidentia-landing-desktop-v42-full-after-cockpit.png`.
- Captura mobile final generada: `qa/evidentia-landing-mobile-v83-hero-title-three-line.png`.
- Revision visual final: H1 mobile sin clipping, chips/mini mirror contenidos y sin blocker horizontal evidente.

### Siguiente paso

1. Limpiar CSS mobile por bloques y retirar overrides duplicados.
2. Grabar/integrar microvideo real de app local con el guion `Intake -> Mirror -> Proof -> Close`.
3. Hacer QA de la seccion `evidence-cockpit` con navegador interactivo real o Playwright operativo.
4. Optimizar assets de video grandes antes de version publica.

### Estado

NO LISTA PUBLICA FINAL - Hay avance de producto/conversion y el mobile hero queda usable, pero no marcaria `READY_FOR_MIGUEL_REVIEW` hasta limpiar CSS mobile y meter el microvideo real.


## 2026-06-30 - Director cut del microvideo y QA de CTA mobile

### Avances de hoy

- Añadi una nueva seccion `director-cut` despues del `product-loop`.
- La seccion convierte el microvideo pendiente en un storyboard interactivo de compra: `Intake -> Mirror -> Proof -> Close`.
- Integra video/motion existente como fondo, overlay narrativo, tabs de escena, guion comercial y senal de compra.
- Reforce el relato de producto: el video debe probar mecanismo, limites, evidencia y decision, no solo verse bonito.
- Hice que `director-cut` no dependa de `IntersectionObserver` para aparecer; queda visible aunque se abra por ancla, captura o scroll rapido.
- Corregi la composicion desktop del bloque: copy full-width arriba y consola debajo para evitar solapamientos.
- Ajuste el CTA mobile `Abrir app local` para que deje de tapar contenido critico durante la lectura.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v40-director-cut-final.png`
  - `qa/evidentia-landing-mobile-v69-director-cut-final.png`
  - `qa/evidentia-landing-desktop-v39-director-cut-final.png`
  - `qa/evidentia-landing-mobile-v68-director-cut-final.png`

### Referencias usadas

- Linear: producto vivo y secuencia de estado comprensible.
- Rive: motion con funcion narrativa, no decoracion.
- Claude Code: autonomia gobernada por revision humana y salida verificable.
- Buyer-guided demo / Arcade-Navattic pattern: guiar al comprador por una prueba pequena antes de pedir fe.

### Decisiones de diseno

- El bloque no promete diagnostico ni decision automatica; el cierre visual es `build / adjust / stop`.
- El microvideo futuro queda especificado como pieza de conversion: entrada real, recuperacion, evidencia, hueco, limite y decision.
- Se priorizo robustez visual frente a una composicion demasiado agresiva: el copy ya no compite con la consola.
- En mobile, el CTA fijo se desactiva en favor de lectura limpia. La web ya tiene CTAs internos suficientes.

### Riesgos

- Sigue faltando grabar el microvideo real de la app local: ingesta -> indexacion -> grafo -> chat RAG -> fuentes -> pack.
- El CSS tiene deuda acumulada de overrides moviles; hoy se corrigio el comportamiento visible, pero conviene una limpieza estructural antes de publicar.
- Las capturas de video/motion actuales son dignas para demo interna, pero la version publica debe sustituir o complementar con uso real grabado.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8892/website.html?v=20260630-director-cut-6`.
- Parser HTML OK con `html.parser`.
- Sintaxis JS inline OK con `new Function(script)`.
- Playwright:
  - Desktop director cut: `scrollWidth=1440`, `clientWidth=1440`, `copyOpacity=1`, `stageOpacity=1`.
  - Mobile director cut: `scrollWidth=390`, `clientWidth=390`, `copyOpacity=1`, `stageOpacity=1`, `dockPosition=static`.
- QA visual con vision sobre capturas finales:
  - Desktop: contenido visible, sin overflow horizontal ni solapamiento critico.
  - Mobile: contenido legible, sin overflow horizontal y CTA sin tapar contenido.

### Siguiente paso

1. Grabar el microvideo real siguiendo el nuevo guion `director-cut`.
2. Limpiar el CSS mobile acumulado y reducir overrides duplicados.
3. Hacer una pasada de ritmo editorial para recortar bloques redundantes antes de publicacion.
4. Decidir si la web publica debe mantener una sola pagina larga o extraer Producto / Confianza / Piloto a paginas separadas.

### Estado

READY_FOR_MIGUEL_REVIEW - La web gana una pieza nueva de storytelling premium y queda mejor preparada para grabar el microvideo real. No la marcaria como final publica hasta integrar ese microvideo y limpiar CSS/mobile.

## 2026-06-29 - Product loop visible y QA de overflow

### Avances de hoy

- Añadi una nueva seccion `product-loop` despues de la prueba visual de app real.
- El bloque convierte la promesa en una escena de producto: `Vault -> Retrieve -> Sources -> Decision`.
- Usa captura real del MVP local como superficie visual, con hotspots, scan animado, tabs interactivos, metricas de etapa y salida defendible.
- Añadi autoplay ligero del loop y controles manuales por estado.
- Reforce el copy comercial: el comprador no necesita magia; necesita ver como una pregunta se convierte en evidencia revisable.
- Corregi un overflow horizontal desktop provocado por `.route-scan` y cerre `overflow-x` tambien en `html`.
- Hice que el nuevo product loop no dependa del reveal observer para aparecer, evitando pantallas invisibles por timing de scroll/captura.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v32-product-loop-final.png`
  - `qa/evidentia-landing-mobile-v60-product-loop-final.png`
  - `qa/evidentia-landing-desktop-v29-fullpage-product-loop.png`
  - `qa/evidentia-landing-mobile-v57-fullpage-product-loop.png`

### Referencias usadas

- Linear: producto vivo como protagonista y estados operativos visibles.
- Rive: motion como cambio de estado, no como adorno.
- Claude Code: autonomia gobernada por trazas, permisos y revision humana.
- Stripe/WorkOS: infraestructura sensible explicada desde control, no desde hype.

### Decisiones de diseño

- La nueva seccion no promete diagnostico ni decision automatica; vende evidencia revisable.
- El loop usa assets reales existentes en vez de una maqueta falsa.
- La interaccion muestra cuatro momentos comprables: entrada, recuperacion, fuentes y decision.
- Mantengo la landing estatica HTML/CSS/JS; no hace falta migrar a React para este nivel de motion.

### Riesgos

- Sigue faltando grabar el microvideo real de uso completo de la app local: subir fuente -> indexar -> grafo -> preguntar -> fuentes -> decision pack.
- El CSS sigue acumulando overrides moviles de iteraciones anteriores; funciona, pero conviene una limpieza antes de publicar fuera.
- En mobile el CTA fijo `Abrir app local` puede tapar contenido bajo en capturas intermedias; no rompe scroll, pero hay que refinar el dock para una version publica.
- La pagina ya es potente pero larga; falta una pasada de ritmo para reducir espacios muertos y ordenar la narrativa final.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8794/website.html`.
- Parser HTML OK con `html.parser`.
- Sintaxis JS inline OK con `new Function(script)`.
- Playwright con Chrome local:
  - Desktop product loop: `scrollWidth=1440`, `clientWidth=1440`, `boardOpacity=1`.
  - Mobile product loop: `scrollWidth=390`, `clientWidth=390`, `boardOpacity=1`.
- Capturas finales revisadas:
  - `qa/evidentia-landing-desktop-v32-product-loop-final.png`
  - `qa/evidentia-landing-mobile-v60-product-loop-final.png`

### Siguiente paso

1. Grabar o montar el microvideo real de app local con flujo completo.
2. Limpiar CSS mobile acumulado y consolidar overrides.
3. Refinar el CTA fijo mobile para que no tape bloques de decision durante capturas/revision.
4. Hacer una pasada de ritmo editorial: menos espacios muertos, mas continuidad entre producto, trust y piloto.

### Estado

READY_FOR_MIGUEL_REVIEW - La web tiene un nuevo bloque de producto real y mejora de QA. Sigue sin ser final publica hasta integrar microvideo real y limpiar mobile/CSS.

## 2026-06-28 - Rutas de adopcion y mobile hero safe

### Avances de hoy

- Reforce el posicionamiento grande de EVIDENTIA como Vector Knowledge Mirror para persona, equipo, centro u organizacion.
- Cambie el hero desktop para dejar de decir "doctor o centro" como comprador principal y abrir el marco a conocimiento sensible organizacional.
- Añadi una nueva seccion `#rutas`: rutas de adopcion por persona experta, equipo, centro/organizacion y primer vertical dental.
- La seccion nueva incluye mapa visual con core local-first, tarjetas flotantes, scan animado y proof comercial de piloto: entrada, test y salida.
- Ajuste el bloque de video para no encerrarlo en ceramica/dental: ahora habla de scattered context -> private knowledge maps.
- Arregle el clipping del hero movil detectado en QA: el parrafo ya no se corta a la derecha y el CTA queda contenido.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v24-routes.png`
  - `qa/evidentia-landing-mobile-v50-routes.png`
  - `qa/evidentia-landing-mobile-v51-routes-fixed.png`
  - `qa/evidentia-landing-mobile-v52-routes-mobile-fix.png`
  - `qa/evidentia-landing-mobile-v53-hero-safe.png`

### Referencias usadas

- Linear: producto vivo y mecanismo visible desde la web, no promesa abstracta.
- Stripe/Clay: infraestructura compleja explicada por rutas de adopcion y compradores diferentes.
- Claude Code: autonomia gobernada por fuentes, permisos y revision humana.
- Rive: motion como estado/proceso; el scan explica recuperacion de conocimiento, no decoracion.
- Pearl/Dandy: dental como vertical natural de confianza y workflow, sin convertir Evidentia en producto clinico cerrado.

### Decisiones de diseño

- Dental queda como primera ruta vendible, no como definicion del producto.
- La nueva seccion `buyer-routes` funciona como puente entre hero y producto: antes de enseñar features, aclara quien compra y por que.
- Mantengo el lenguaje premium oscuro/iridiscente, pero con copy mas sobrio para privacidad, fuentes y control.
- En mobile priorice lectura segura sobre espectacularidad: el hero queda mas compacto y menos arriesgado.

### Riesgos

- La CSS movil sigue acumulando overrides de muchas iteraciones. Funciona para el hero actual, pero conviene una limpieza tecnica antes de publicar fuera.
- Las capturas directas con ancla `#rutas` salieron demasiado pequeñas/blancas por comportamiento raro de Chrome headless; use capturas de pagina y revision visual del hero movil como gate principal.
- Chrome headless queda a veces vivo tras escribir screenshot en este entorno; limpie los procesos de QA nuevos, pero hay procesos antiguos de capturas previas que no toque.
- Falta todavia el microvideo real de uso local: subir fuente -> indexar -> grafo -> preguntar -> fuentes -> decision pack.

### Verificacion

- Servidor local usado: `http://127.0.0.1:8793/website.html`.
- `curl -I` OK para `website.html` y `website.css`.
- Parser HTML OK con `html.parser`.
- Sintaxis JS inline OK con `new Function(script)`.
- Captura desktop generada: `qa/evidentia-landing-desktop-v24-routes.png`.
- Captura mobile final generada: `qa/evidentia-landing-mobile-v53-hero-safe.png`.
- Revision visual automatica final: hero mobile sin clipping horizontal.

### Siguiente paso

1. Grabar/integrar microvideo real del flujo de app local completo.
2. Hacer limpieza CSS mobile para retirar overrides defensivos duplicados.
3. QA de `#rutas` en navegador real o Playwright con scroll controlado, porque Chrome headless por fragmento dio capturas no fiables.
4. Comprimir assets de video y preparar variante publica ligera.

### Estado

READY_FOR_MIGUEL_REVIEW - La landing queda mejor posicionada y revisable por Miguel. No la venderia como final publica hasta integrar microvideo real, limpiar CSS mobile y hacer QA manual en navegador real.



## 2026-06-26 - Simulador de piloto y demo comprable

### Avances de hoy

- Añadi una nueva seccion `pilot-simulator` en `website.html` entre la microdemo local-first y `Ask the mirror`.
- La seccion convierte el piloto en una demo guiada por comprador: `Intake -> Mirror run -> QA gate -> Decision`.
- Cada fase cambia copy, output, metrica y visual central mediante tabs clicables.
- Refuerza la venta como prueba pequeña, seria y medible antes de ampliar alcance.
- Actualice el cache-buster de `website.css` a `20260626-pilot-simulator`.
- Añadi CSS responsive especifico para el simulador, mas guardrails finales de mobile para reducir cortes en hero, tabs y CTA flotante.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA nuevas:
  - `qa/evidentia-landing-desktop-v21-simulator.png`
  - `qa/evidentia-landing-mobile-v41-simulator.png`
  - `qa/evidentia-landing-desktop-v22-simulator-safe.png`
  - `qa/evidentia-landing-mobile-v42-simulator-safe.png`
  - `qa/evidentia-landing-mobile-v43-simulator-safe-tabs.png`

### Referencias usadas

- Navattic / Arcade: buyer-guided demo, enseñar el flujo segun la decision que el comprador necesita tomar.
- Momentic: QA before delivery, marcar huecos y no vender una salida como valida sin revision.
- Linear: producto vivo, estados visibles y sensacion de sistema operativo.
- Harvey / WorkOS / Stripe: trust stack sensible, fronteras y decision audit-ready.

### Decisiones de diseño

- Mantener stack estatico HTML/CSS/JS: rapido, publicable y suficiente para una landing premium si los assets estan bien elegidos.
- No vender EVIDENTIA como producto clinico ni dental-only: el simulador habla de conocimiento sensible, memoria privada y decision humana.
- Hacer que el piloto tenga una salida comprable: `Memory report + roadmap de 30 dias + build / adjust / stop`.
- Usar motion CSS y microinteraccion real antes de meter una libreria pesada.
- Priorizar guardrails mobile al final del CSS porque el archivo acumula varias capas previas de fixes.

### Riesgos

- La captura visual automatica aun marco problemas de mobile en la zona de tabs/dock antes del ultimo guardrail; hace falta una revision manual en movil real o CDP estable.
- Sigue faltando el microvideo real de uso de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
- Las capturas de producto siguen siendo QA local; antes de publicar conviene seleccionar definitivas y optimizarlas.
- El CSS tiene muchas capas historicas de parches mobile; una limpieza posterior mejoraria mantenibilidad.

### Verificacion

- Parser HTML OK con `html.parser`.
- Servidor local existente responde en `http://127.0.0.1:8806/website.html`.
- `curl -I` OK para `website.html`, `website.css` y video hero.
- Chrome headless genero capturas desktop/mobile indicadas arriba.
- Vision QA:
  - Desktop sin cortes ni solapes graves.
  - Mobile detecto cortes en tabs/dock antes del ultimo guardrail; se aplico ajuste final a tabs 1-columna, CTA flotante con margen seguro y mas padding inferior.

### Siguiente paso

1. Validar mobile real despues del guardrail final, idealmente con CDP estable o navegador fisico.
2. Grabar microvideo real de app local: ingesta -> entidades/grafo -> chat RAG -> fuentes -> pack.
3. Sustituir el video narrativo por una prueba de uso real o complementarlo con un clip de producto.
4. Limpiar CSS mobile acumulado y dejar un sistema responsive menos parcheado.
5. Hacer pasada de performance por peso de video/imagenes antes de publicar.

### Estado

NO_READY_FOR_FINAL_PUBLISH - Hoy la web gana una pieza comercial importante: el piloto ya se entiende como demo comprable y decision de negocio. Sigue lista para revision interna de Miguel, pero no la marcaria como publicacion final hasta validar mobile real y meter el microvideo de producto.

## 2026-06-24 - Feedback directo de Miguel: no confundir app con web

Miguel pidio revisar la pagina web de EVIDENTIA, no la aplicacion local. Error operativo detectado: se abrio primero `index.html`, que es la app, cuando la revision que queria era `website.html`.

### Mandato corregido para Faki

- La web debe sentirse como web comercial/publica, no como la aplicacion abierta.
- Miguel espera varias paginas o, como minimo, arquitectura navegable clara: home, producto, pilotos/casos, confianza/privacidad, primer vertical dental y contacto/demo.
- Debe tener movimiento y video real o microvideo de producto, tal como se habia hablado.
- La app se revisara aparte; no usar la app como sustituto de la web.
- La web actual puede estar lista para una primera revision, pero no se debe vender como cierre final si aun falta multipagina/motion/video real.

### Accion inmediata

- Abrir para Miguel: `http://127.0.0.1:8888/website.html?v=20260622-good-web-restore`.
- Siguiente mejora de Faki: convertir la landing en experiencia web mas navegable y preparar el microvideo real de producto.

## 2026-06-24 - Correccion inmediata: web navegable y video visible

Miguel volvio a corregir que no veia el video prometido y que la web seguia pareciendo incompleta, con paginas/secciones sueltas sin una arquitectura clara.

### Cambios aplicados

- Actualizada `website.html` para abrir una capa de web publica completa bajo `#web`.
- Anadida arquitectura navegable con seis paginas internas llenas: Home, Producto, Dental, Confianza, Piloto y Contacto.
- Anadido bloque `#video-producto` con video visible, controles y explicacion de la secuencia: entrada, conexion y salida.
- La navegacion superior ahora lleva a Web, Video, Producto, Confianza y Piloto.
- Actualizado cache-buster CSS a `20260624-complete-web-video`.

### Verificacion

- Parser HTML OK.
- `website.html`, `website.css` y el MP4 hero responden 200 en `http://127.0.0.1:8888/`.
- Comprobacion DOM: existe `site-pages`, `product-video`, seis paneles `data-page-panel`, fuente MP4 y script `setPage`.

### Pendiente real

La web ya no esta vacia ni solo como app, pero para quedar al nivel que Miguel quiere falta grabar o montar el microvideo real de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack. El video actual es motion del knowledge map, no todavia captura real de uso.

## 2026-06-24 - Octava pasada: trace ledger y evidencia defendible

### Avances

- Añadi una nueva seccion `trace-ledger` despues del trust stack.
- La seccion convierte la promesa de trazabilidad en una escena de producto: consulta, fuentes fuertes, hueco bloqueante, gate humano y salida defendible.
- Refuerza el posicionamiento premium de EVIDENTIA: no gana por responder rapido, gana porque puede explicar de donde sale cada respuesta.
- Compacte el comportamiento mobile del ledger para que las tarjetas aparezcan antes y no se sienta como una pausa vacia.
- Actualice el cache-buster del CSS a `20260624-trace-ledger`.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md
- Capturas QA nuevas:
  - qa/evidentia-landing-desktop-v18.png
  - qa/evidentia-landing-mobile-v36-simple.png
  - qa/evidentia-landing-mobile-v36-cdp.png
  - qa/evidentia-landing-mobile-v36-ledger.png

### Referencias usadas

- Middesk: investigacion audit-ready, salida defendible y decision humana.
- Watershed: pipeline trazable con metodologia, fuentes y control.
- Linear: producto vivo y sistema visible en vez de claims abstractos.

### Decisiones de diseño

- No introducir stack nuevo; la landing estatica sigue siendo suficiente para publicar y mantener rapido.
- Usar el nuevo ledger como bloque de confianza/conversion, no como decoracion.
- Mantener dental fuera del centro del bloque: la trazabilidad aplica a cualquier equipo sensible que construye memoria local-first.
- Seguir evitando claims clinicos o porcentajes no validados.

### Riesgos

- Sigue faltando el microvideo real de uso de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
- La seccion ledger es una representacion de producto; debe calibrarse con una corrida real cuando Miguel cargue material anonimo.
- Antes de publicar conviene revisar el peso final de capturas/video y hacer una pasada manual en movil real.

### Siguiente paso

1. Grabar microvideo real de navegacion dentro de la app local y colocarlo como prueba principal.
2. Elegir capturas definitivas y optimizarlas para produccion.
3. Revisar performance/Lighthouse y sensacion de scroll en un movil real.
4. Cerrar el copy final del piloto con inputs exactos y criterio de exito.

### Verificacion

- Parser HTML OK con `html.parser`.
- Servidor temporal local: http://localhost:8795/website.html.
- curl -I OK para `website.html`, `website.css` y video hero.
- Chrome headless:
  - desktop 1440x2600: `qa/evidentia-landing-desktop-v18.png`.
  - mobile simple: `qa/evidentia-landing-mobile-v36-simple.png`.
  - mobile CDP real 390px: `qa/evidentia-landing-mobile-v36-cdp.png`.
  - mobile ledger: `qa/evidentia-landing-mobile-v36-ledger.png`.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport 390.
  - documentElement.scrollWidth = 390.
  - body.scrollWidth = 390.
  - sin nodos fuera del viewport.
  - `.trace-ledger` dentro de left=0, right=390.
- QA visual:
  - top mobile sin clipping ni solapes visibles.
  - ledger mobile legible, mas compacto tras ajuste, sin overflow real.

### Estado

READY_FOR_MIGUEL_REVIEW - La web sigue lista para revision real y hoy gana una capa importante de confianza: trazabilidad defendible. Para quedar brutal de verdad falta el microvideo real de la app local y optimizacion final de assets.

## 2026-06-23 - Septima pasada: cierre comercial del piloto y decision room

### Avances

- Añadi una nueva seccion `pilot-room` entre el piloto de 7 dias y el roadmap.
- La seccion convierte el piloto en una decision comprable: construir, ajustar o parar.
- Refuerza que EVIDENTIA no vende magia ni diagnostico: vende una prueba con fuentes visibles, huecos y siguiente roadmap.
- Añadi un `decision-board` con pregunta de evaluacion, tres salidas posibles y entregable vendible: memory report + roadmap de 30 dias + datos faltantes.
- Actualice el cache-buster del CSS a `20260623-pilot-room`.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md

### Referencias usadas

- Middesk: investigacion audit-ready y decision humana como salida del sistema.
- Linear: producto vivo con estados visibles, no promesa abstracta.
- Tines / LangSmith: matriz operativa para decidir si algo pasa a flujo, se ajusta o se detiene.

### Decisiones de diseño

- No rehacer la web porque el estado anterior ya estaba en READY_FOR_MIGUEL_REVIEW.
- Priorizar conversion: que Miguel pueda vender un piloto cerrado y no una demo generica.
- Mantener los numeros como señales de piloto, no claims validados.
- Mantener el stack estatico HTML/CSS/JS porque sigue siendo suficiente y ligero para publicar.

### Riesgos

- Sigue faltando el microvideo real de uso de la app local como prueba principal.
- Antes de publicar conviene seleccionar capturas definitivas y comprimir video/imagenes.
- El nuevo decision room es narrativo; debe calibrarse con resultados reales de una corrida con material anonimo.

### Siguiente paso

1. Grabar microvideo real de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
2. Sustituir o complementar el playback narrativo con esa navegacion real.
3. Hacer QA visual final en navegador real mobile/desktop y revisar performance.
4. Cerrar copy comercial del piloto de 7 dias con inputs exactos y criterios de exito.

### Verificacion

- Parser HTML OK con `html.parser`.
- Servidor temporal local: http://localhost:8794/website.html.
- curl -I OK para `website.html`, `website.css` y video hero.
- Chrome headless:
  - desktop 1440x2600: `qa/evidentia-landing-desktop-v17.png`.
  - mobile simple 390x3000: `qa/evidentia-landing-mobile-v33.png` marco falso positivo de clipping por no emular viewport movil real.
  - mobile CDP real 390px: `qa/evidentia-landing-mobile-v35-cdp-visible.png`.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport 390.
  - documentElement.scrollWidth = 390.
  - body.scrollWidth = 390.
  - sin overflow horizontal real.
- QA visual sobre cortes CDP revelados:
  - `qa/evidentia-landing-mobile-v35-top.png`.
  - `qa/evidentia-landing-mobile-v35-pilot.png`.
  - sin clipping, overflow, assets rotos ni solapes bloqueantes visibles.

### Estado

READY_FOR_MIGUEL_REVIEW - La web sigue lista para revision y hoy gana un cierre comercial mas defendible. Para quedar brutal de verdad falta el microvideo real y seleccion final de assets.

## 2026-06-22 - Sexta pasada: prueba visual, mirror reel y hardening mobile

### Avances

- Reforce la landing publica con una seccion `product-proof` que enseña capturas reales del MVP local: desktop y mobile.
- Añadi `mirror-reel`, un playback interactivo con tres escenarios comprables: Clinica, Laboratorio y Equipo experto.
- El playback cambia intake, estructuracion, recuperacion, salida y ledger de piloto sin vender metricas clinicas como validadas.
- Añadi `signal-console` para explicar como se juzga el piloto: busquedas evitadas, decisiones mejor preparadas y conocimiento transferible.
- Añadi roadmap v1/v2/v3 para elevar la tesis de EVIDENTIA como memoria privada consultable -> atlas de criterio -> organizacion que aprende.
- Añadi CTA movil flotante `Abrir app local` y corregi el overflow/corte mobile detectado en QA.
- Actualice el cache-buster del CSS a `20260622-mirror-reel`.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md
- Capturas QA nuevas:
  - qa/evidentia-landing-desktop-v15.png
  - qa/evidentia-landing-mobile-v26.png
  - qa/evidentia-landing-mobile-v27.png
  - qa/evidentia-landing-mobile-v28.png
  - qa/evidentia-landing-mobile-v29.png
  - qa/evidentia-landing-mobile-v30.png

### Referencias usadas

- Linear: producto visible desde la landing, no solo declaracion estrategica.
- Rive: motion/estado como explicacion del proceso intake -> structure -> retrieve -> review.
- LangSmith / Decagon: trazas, ledger operativo y señales para evaluar un sistema agentico.
- Q Bio / Maven Clinic: baseline contextual y confianza por momentos, sin convertir EVIDENTIA en producto clinico.

### Decisiones de diseño

- Mantener stack estatico HTML/CSS/JS: suficiente para una landing publicable, ligera y facil de servir.
- Usar capturas reales disponibles en `qa/` como proof inmediato mientras falta el microvideo real.
- Presentar dental como primer vertical natural, pero reforzar tambien equipo experto y organizacion.
- En mobile, sacrificar parte del display condensado por Inter pesada en titulares para evitar cortes y mejorar lectura.
- Forzar un guardrail mobile de anchura segura para que el CTA y los paneles no rompan en 390px.

### Riesgos

- Sigue faltando grabar un microvideo real de uso dentro de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
- Las capturas de producto vienen de QA local; antes de publicar conviene elegir las definitivas y optimizarlas.
- El playback interactivo es una demostracion narrativa, no una corrida real de datos de Miguel. Debe sustituirse o calibrarse cuando haya material anonimo cargado.
- El hardening mobile esta aprobado en 390px, pero conviene revisar manualmente en navegador real iPhone/Android antes de produccion.

### Siguiente paso

1. Grabar microvideo real de navegacion dentro de la app local y colocarlo como prueba principal.
2. Elegir capturas definitivas de producto y optimizarlas para peso/performance.
3. Pulir el copy final de conversion para un piloto de 7 dias con paquete de inputs claro.
4. QA manual en navegador real y Lighthouse/performance antes de publicar.

### Verificacion

- Parser HTML OK con `html.parser`.
- Servidor temporal local: http://localhost:8793/website.html.
- curl -I OK para `website.html` y `website.css`.
- Chrome headless:
  - desktop 1440x2400: `qa/evidentia-landing-desktop-v15.png`.
  - mobile 390x2600: `qa/evidentia-landing-mobile-v30.png`.
- QA visual por imagen:
  - mobile v26-v29 detectaron overflow/corte; se corrigio con hardening mobile y CTA full-width.
  - mobile v30 aprobado: CTA completo y sin clipping lateral relevante.

### Estado

READY_FOR_MIGUEL_REVIEW - La web ya tiene video hero, proof visual, playback interactivo, señales de piloto, roadmap, CTA mobile y QA basico. Para quedar brutal de verdad falta el salto de produccion: microvideo real de uso de la app y seleccion final de capturas.

## 2026-06-21 - Quinta pasada: mirror playback interactivo

### Avances

- Converti la microdemo local-first en una demo mas viva con selector de escenarios: Clinica, Laboratorio y Equipo experto.
- Añadi un modulo mirror playback con barras de confianza, log de evidencias y cambios de copy/fuentes/veredicto por escenario.
- El bloque ahora comunica mejor que EVIDENTIA no es solo una promesa visual: el comprador puede ver como cambia una corrida del mirror segun el contexto del cliente.
- Actualice el cache-buster del CSS a 20260621-live-recorder.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md
- Capturas QA nuevas:
  - qa/evidentia-landing-desktop-v13.png
  - qa/evidentia-landing-mobile-v23.png
  - qa/evidentia-landing-desktop-v14-long.png
  - qa/evidentia-landing-mobile-v24-long.png
  - qa/evidentia-landing-mobile-v25-cdp.png

### Referencias usadas

- Linear: producto vivo, estados visibles y UI que demuestra sistema.
- Rive: motion/interaccion como explicacion de estado, no ornamento.
- Granola / Abridge: narrar momentos de trabajo reales y convertir contexto en salida revisable.

### Decisiones de diseño

- Mantener HTML/CSS/JS estatico porque la interaccion necesaria sigue siendo ligera y publicable sin stack pesado.
- Usar escenarios de compra en vez de tabs tecnicas: clinica, laboratorio y equipo experto.
- Las barras no se presentan como metricas validadas; son señales de lectura del mirror dentro de la demo.
- Seguir marcando la frontera correcta: la IA prepara contexto y el experto valida.

### Riesgos

- Todavia falta grabar un microvideo real de uso dentro de la app local. Este playback interactivo sube credibilidad, pero no sustituye una navegacion real.
- Los escenarios son copy de demo y deben calibrarse con una corrida real de datos de Miguel cuando exista material anonimo cargado.
- Antes de publicar conviene una pasada manual en navegador real para sensacion de scroll, performance del video hero y foco de botones.

### Siguiente paso

1. Grabar microvideo real de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
2. Sustituir parte del mock/playback por video real o combinar ambos.
3. Revisar accesibilidad de botones/foco y performance mobile del video.
4. Preparar una version comercial corta con CTA a piloto de 7 dias y paquete de inputs.

### Verificacion

- Parser HTML OK con html.parser.
- Servidor temporal local: http://localhost:8792/website.html.
- curl -I OK para website.html y website.css.
- Chrome headless:
  - desktop 1440x2400: qa/evidentia-landing-desktop-v13.png.
  - mobile 390x2600: qa/evidentia-landing-mobile-v23.png.
  - desktop largo 1440x5600: qa/evidentia-landing-desktop-v14-long.png.
  - mobile largo 390x5600: qa/evidentia-landing-mobile-v24-long.png.
  - mobile emulado via CDP 390x5600: qa/evidentia-landing-mobile-v25-cdp.png.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport 390.
  - documentElement.scrollWidth = 390.
  - body.scrollWidth = 390.
  - sin nodos fuera del viewport.
  - .problem h2 dentro de left=32, right=358, width=326.
  - .demo-recorder dentro de left=51, right=339, width=288.
- Interaccion verificada via CDP: al seleccionar Laboratorio cambian escenario activo, label, fuente principal y veredicto.

### Estado

READY_FOR_MIGUEL_REVIEW - La web sigue lista para revision real y hoy gana interaccion de producto. Para quedar brutal de verdad, el siguiente salto sigue siendo video real de navegacion de la app.

## 2026-06-20 - Cuarta pasada: microdemo local-first

### Avances

- Añadi una nueva seccion local-demo despues de la prueba visual de producto.
- La seccion muestra una corrida concreta del mirror: intake -> structure -> retrieve -> review.
- Refuerza la tesis de que EVIDENTIA no es un chat: es infraestructura local-first para convertir material propio en memoria vectorial verificable.
- Añadi consola visual con pregunta realista, fuentes recuperadas y human gate.
- Actualice el cache-buster del CSS para forzar la version nueva.
- Ajuste preventivo de wrapping mobile en el texto grande de la microdemo.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md
- Capturas QA nuevas:
  - qa/evidentia-landing-desktop-v12.png
  - qa/evidentia-landing-mobile-v22.png

### Referencias usadas

- Linear: producto vivo y estados operativos visibles.
- Granola / Abridge: narrar momentos reales de trabajo, no promesas abstractas.
- Rive: motion de estado para explicar proceso y no decorar.

### Decisiones de diseño

- La nueva franja se coloca justo despues de las capturas reales para convertir la prueba visual en secuencia de uso.
- El copy evita vender diagnostico o decision automatica; remata en revision humana.
- Se mantienen numeros ilustrativos como señales de demo, no como claim comercial validado.
- El motion se limita a barras, fuentes y estado de pipeline para conservar rendimiento y lectura mobile.

### Riesgos

- Sigue faltando un microvideo real grabado desde la app local; esta seccion lo simula de forma digna, pero el siguiente salto es video real de navegacion.
- Las metricas de la microdemo son ejemplos de storytelling y deben sustituirse por una corrida real cuando Miguel cargue material propio.
- La revision visual automatica marco posible clipping en mobile en una seccion anterior, aunque la medicion DOM no encontro overflow.

### Siguiente paso

1. Grabar microvideo real de la app local: ingesta -> grafo -> chat RAG -> fuentes.
2. Sustituir la microdemo CSS por video/captura viva o combinar ambos.
3. Hacer QA manual en navegador real y revisar performance de video en movil.
4. Preparar una version corta para demo comercial con CTA a piloto de 7 dias.

### Verificacion

- Parser HTML OK con html.parser.
- Servidor temporal local: http://localhost:8791/website.html.
- curl -I OK para website.html, website.css y video hero.
- Chrome headless:
  - desktop 1440x2200: qa/evidentia-landing-desktop-v12.png.
  - mobile 390x2400: qa/evidentia-landing-mobile-v22.png.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport 390.
  - documentElement.scrollWidth = 390.
  - body.scrollWidth = 390.
  - sin nodos fuera del viewport.
  - .local-demo dentro de left=32, right=358, width=326.
  - .problem h2 dentro de left=32, right=358, width=326.

### Estado

READY_FOR_MIGUEL_REVIEW - La web sigue en calidad de revision real y hoy sube credibilidad con una secuencia de producto mas concreta. Para quedar brutal de verdad, falta reemplazar parte de esta simulacion por microvideo real de uso.

## 2026-06-19 - Tercera pasada: consola de señales y limites

### Avances

- Añadi una seccion nueva signal-console entre confianza y casos de uso.
- La seccion traduce el piloto en señales comprables: fuentes recuperadas, huecos detectados y criterios reutilizables.
- Reforce el limite de producto con dos bloques claros:
  - lo que si vende: memoria privada con evidencia.
  - lo que no promete: no diagnostica ni decide por el experto.
- Actualice el cache-buster del CSS para forzar la version nueva.
- Tras QA mobile, ajuste el wrapping de titulares para evitar cortes laterales en pantallas estrechas.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md

### Referencias usadas

- Linear: producto vivo y estados de sistema como prueba.
- WorkOS / Harvey: confianza sensible, readiness y limites claros.
- Decagon: consola de operacion y senales medibles en vez de promesa abstracta.

### Decisiones de diseño

- La nueva franja evita que la landing dependa solo del impacto visual: ahora enseña como se juzga un piloto.
- Se mantiene dental como primer vertical implicito, pero el copy sigue hablando de equipo/organizacion y memoria vectorial privada.
- Se explicita una frontera comercial importante: EVIDENTIA prepara contexto verificable, no automatiza decisiones sensibles.

### Riesgos

- Sigue faltando el microvideo real de uso dentro de la app para que la prueba de producto suba un nivel mas.
- La consola usa numeros ilustrativos de piloto; conviene sustituirlos por metricas reales cuando Miguel haga una demo con datos propios.
- Las capturas nuevas validan estructura general, pero conviene una revision manual en navegador real antes de publicar.

### Siguiente paso

1. Grabar microvideo real de la app local: ingesta -> grafo -> chat RAG -> fuentes.
2. Reemplazar numeros de consola por resultados de una corrida real del piloto.
3. Hacer QA visual desktop/mobile de esta tercera pasada y ajustar si aparece overflow.

### Verificacion

- Parser HTML OK con html.parser.
- Servidor temporal local: http://localhost:8790/website.html.
- curl -I OK para website.html, website.css y video hero.
- Chrome headless:
  - desktop 1440x2200: qa/evidentia-landing-desktop-v11.png.
  - mobile 390x2200: qa/evidentia-landing-mobile-v20.png.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport 390.
  - documentElement.scrollWidth = 390.
  - body.scrollWidth = 390.
  - .problem h2 dentro de left=32, right=358, width=326.
  - sin nodos fuera del viewport.

### Estado

READY_FOR_MIGUEL_REVIEW - La web sigue lista para revision de Miguel, ahora con una capa mas fuerte de compra: señales, limites y criterios de piloto.

## 2026-06-19 - Segunda pasada produccion premium

### Avances

- Reforce la landing publica con prueba visual real de producto: nueva seccion `product-proof` con capturas locales desktop/mobile de la app.
- Añadi narrativa `Ask the mirror`: pregunta -> recuperacion -> mapa -> decision humana, para explicar el mecanismo sin caer en claims genericos.
- Añadi roadmap v1/v2/v3 como capa de ambicion marcada explicitamente como evolucion, no promesa inflada.
- Ajuste el hero:
  - elimine el banner duplicado superior de EVIDENTIA que competia con el H1.
  - compacte el primer viewport movil.
  - añadi telemetria de producto y gate de revision humana.
- Añadi barra CTA movil superior `Abrir app local` para asegurar acceso claro sin tapar contenido como ocurria con el dock fijo.
- Añadi `IntersectionObserver` para reveals progresivos en secciones de producto, confianza, casos y roadmap.
- Endureci mobile: anchura de secciones mas conservadora, headings menos agresivos y wrapping normal para evitar particiones visualmente feas.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA nuevas:
  - `qa/evidentia-landing-desktop-v10.png`
  - `qa/evidentia-landing-mobile-v18.png`
  - crops/iteraciones intermedias `mobile-v9` a `mobile-v18` usadas para depuracion visual.

### Verificacion

- `html.parser` OK.
- Servidor temporal local: `http://localhost:8788/website.html`.
- `curl -I` OK para `website.html` y `website.css`.
- Chrome headless:
  - desktop `1440x1800`: `qa/evidentia-landing-desktop-v10.png`.
  - mobile `390x1900`: `qa/evidentia-landing-mobile-v18.png`.
- Medicion DOM mobile via Chrome DevTools Protocol:
  - viewport `390`.
  - `documentElement.scrollWidth = 390`.
  - `body.scrollWidth = 390`.
  - sin nodos ofensores fuera del viewport.
  - `.problem h2` dentro de `left=32`, `right=358`, `width=326`, sin overflow CSS.

### Estado

READY_FOR_MIGUEL_REVIEW - La web ya tiene video, movimiento, narrativa premium, prueba visual de producto real, CTA movil y QA desktop/mobile. Siguiente mejora recomendable: grabar microvideo real de uso dentro de la app para sustituir parte del mock conceptual por navegacion viva.

## 2026-06-18 - Capa de piloto ejecutable y QA mobile

### Avances de hoy

- Añadi una nueva seccion `pilot-blueprint` antes del CTA final para convertir la landing en una propuesta de piloto medible, no solo una demo visual.
- La seccion explica un piloto de 7 dias con tres fases:
  - Mirror seed: 50-200 piezas, taxonomia, permisos y separacion de material sensible.
  - Retrieval test: preguntas reales, fuentes, huecos, contradicciones y utilidad por rol.
  - Decision pack: informe de que sabe el sistema, que no sabe, donde ahorra tiempo y que siguiente capa merece construirse.
- Añadi un ledger de metricas de conversion: busquedas evitadas, fuentes completas y criterio reutilizable.
- Ajuste el hero mobile tras QA visual: el badge superior de EVIDENTIA ya no se corta y el primer viewport tiene menos aire muerto antes del contenido.
- Actualice el cache-buster del CSS para forzar la nueva capa visual.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v6.png`
  - `qa/evidentia-landing-mobile-v6.png`
  - `qa/evidentia-landing-mobile-v7.png`
  - `qa/evidentia-landing-mobile-v8.png`

### Referencias usadas

- WorkOS / Harvey: confianza sensible y readiness stack antes de pedir compromiso.
- Decagon: piloto/lifecycle visible, medible y orientado a operacion.
- Linear: producto y proceso como prueba visual, no claims abstractos.

### Decisiones de diseño

- La landing ahora vende un camino de compra mas claro: no "mira una demo", sino "carga contexto real y mide si el mirror recupera valor".
- El piloto se formula sin prometer porcentajes ni resultados no probados; usa metricas observables.
- La nueva seccion mantiene el lenguaje amplio de Vector Knowledge Mirror y evita encerrar EVIDENTIA en dental.
- En mobile, el badge decorativo se fija con `left/right` reales en lugar de centrado transformado para evitar clipping.

### Riesgos

- Falta integrar capturas o microvideo de producto real de la app para subir credibilidad por encima del mock CSS.
- La pagina ya es usable, pero aun necesita una pasada de performance/accesibilidad y QA manual en navegador real.
- Conviene convertir el plan de piloto en un CTA mas accionable cuando Miguel defina el paquete comercial exacto.

### Verificacion

- Parser HTML OK con `html.parser`.
- Servidor temporal local con `python3 -m http.server 8787`.
- `curl -I` OK para `website.html`, `website.css` y video hero.
- Capturas Chrome headless:
  - desktop `1440x1800`: `qa/evidentia-landing-desktop-v6.png`
  - mobile `390x1900`: `qa/evidentia-landing-mobile-v8.png`
- Revision visual mobile final: OK, sin badge cortado, sin solapes obvios ni overflow horizontal visible.

### Siguiente paso

1. Generar o grabar microvideo real de producto navegando ingesta -> grafo -> chat RAG -> fuentes.
2. Integrar 2-3 pantallas reales de la app en la seccion `Producto vivo`.
3. Pulir accesibilidad/performance: contraste, foco, labels, peso de video y fallback.
4. Hacer QA manual desktop/mobile con navegador real.

### Estado

NOT_READY_YET - Avance fuerte en conversion y claridad de piloto, pero falta prueba visual real del producto para marcar `READY_FOR_MIGUEL_REVIEW`.

## 2026-06-18 - Iteracion premium mirror

### Avances de hoy

- Rehice la landing publica `website.html` como pagina premium de posicionamiento, no como prototipo generico.
- Nuevo hero cinematografico con video existente, marca EVID&#398;NTIA fuerte, promesa clara de Vector Knowledge Mirror y CTA directo a la app local.
- Anadi mock visual interactivo del producto: live mirror, orbitas de memoria, pregunta recuperada, fuentes y chips de evidencia.
- Reestructure la narrativa:
  - problema de perdida de contexto
  - producto vivo verificable
  - flujo captura -> estructura -> recupera -> decide
  - trust stack local-first
  - casos de uso mas alla de dental
  - CTA de piloto de conocimiento
- Reescribi el CSS completo con dark premium, gradiente iridiscente controlado, glass panels, motion ligero, scroll meter, hover states y responsive mobile.
- Corregi overflow mobile detectado en QA: hero, CTA, card de pregunta y chips ya no se cortan en captura 390px.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas en `qa/`:
  - `qa/evidentia-landing-desktop-v2.png`
  - `qa/evidentia-landing-mobile-v5.png`

### Referencias usadas

- Linear: producto vivo y UI como prueba, no promesa abstracta.
- Harvey / WorkOS: confianza sensible, permisos, auditoria, local-first y control de datos.
- Rive / Arcade: motion y visual de producto como storytelling, no decoracion.
- Vertical AI interno: fondo negro, display condensado, gradiente iridiscente y tono Faki de IA premium.

### Decisiones de diseno

- EVID&#398;NTIA se posiciona como memoria contextual local-first para personas, equipos, centros y organizaciones.
- Dental queda como primer vertical natural, no como limite del producto.
- La IA no se vende como decision automatica: prepara contexto, enseña fuentes y deja la decision humana.
- El video existente se mantiene como textura de producto, reforzado con overlay y mock UI propio.
- Se evita lenguaje clinico-regulatorio fuerte para no venderlo como producto medico.

### Riesgos

- La landing ya tiene impacto visual, pero las secciones inferiores necesitan una segunda pasada de fine tuning: ritmo, microinteracciones, densidad y posible integracion de capturas reales de la app.
- El mock del producto es CSS conceptual; conviene sumar capturas reales o video corto de la app para aumentar credibilidad.
- Falta QA interactivo manual en navegador real, no solo capturas headless.
- No esta marcada como final publicable todavia.

### Verificacion

- Servidor local levantado: `http://localhost:8787/website.html`
- `curl -I` OK para:
  - `website.html`
  - `website.css`
  - `assets/evidentia/evidentia-hero.mp4`
  - `assets/evidentia/evidentia-hero-poster.jpg`
- Parser HTML OK con `html.parser`.
- Capturas headless generadas con Google Chrome:
  - desktop 1440x1200
  - mobile 390x1200

### Siguiente paso

1. Grabar o generar un microvideo de producto real navegando la app: ingesta, grafo, chat RAG, pack.
2. Afinar secciones posteriores con sticky storytelling o timeline scroll-driven.
3. Meter una capa de conversion mas concreta: piloto de 7 dias, inputs requeridos, entregables y metrica de exito.
4. Revisar performance y accesibilidad basica.
5. Preparar version final para Miguel con criterio `READY_FOR_MIGUEL_REVIEW` solo cuando pase QA visual completo.

### Estado

NOT_READY_YET - La direccion ya es premium y usable, pero falta una iteracion de producto real/capturas y polish final para decir que esta brutal.

## 2026-06-18 - Benchmark profundo y direccion final

### Avances

- Lei FAKI_WEB_BRIEF.md, la biblioteca Faki de referencias y el estado actual de la web/progreso.
- Contraste referencias externas y patrones reales de Linear, Granola, Notion AI, Abridge, Decagon, Rive y productos de memoria/contexto.
- Actualice FAKI_WEB_BRIEF.md con una direccion creativa final producible:
  - benchmark operativo por referencia
  - posicionamiento como Vector Knowledge Mirror
  - estructura final de 9 secciones
  - direccion visual y motion system
  - assets necesarios
  - copy base
  - riesgos creativos/producto
  - plan de produccion por fases
  - criterio de aprobacion Faki

### Decision clave

La siguiente iteracion debe priorizar producto real visible antes que framework: capturas, microvideo de app local, dataset demo anonimo y sticky product narrative. HTML/CSS/JS estatico sigue siendo suficiente salvo que el motion interactivo exija estado complejo.

### Estado

BRIEF_READY_FOR_PRODUCTION_DIRECTION - El documento ya puede guiar una reconstruccion premium. La web sigue NOT_READY_YET hasta integrar producto real/capturas y pasar QA visual desktop/mobile.
## 2026-06-25 - Prueba operativa above-the-fold y QA mobile

### Avances de hoy

- Reforce el hero publico para que venda una accion concreta: probar el mirror local, no solo abrir una app.
- Reescribi el copy mobile del primer viewport con una promesa mas defendible: subir casos, audios, PDFs y protocolos para obtener una memoria privada con fuentes, huecos y revision humana.
- Añadi un mini `live mirror` especifico para mobile dentro del hero, con secuencia compacta: pregunta -> fuentes -> hueco bloqueante -> decision preparada.
- Añadi la seccion `evidence-strip` justo despues del hero para explicar la prueba operativa inmediata:
  - input real de 50-200 piezas
  - mirror run con 10 preguntas reales
  - decision pack y roadmap de 30 dias
- Cambie CTAs principales a lenguaje mas conversional:
  - `Probar mirror local`
  - `Ver prueba operativa`
- Ajuste CSS mobile conservador:
  - CTA mobile fijo al fondo sin cortar contenido
  - `body` con padding inferior para evitar que el dock tape tabs
  - hero mobile con ancho maximo controlado
  - mini mirror apilado y sin elemento visual invadiendo texto
- Actualice cache-buster del CSS.

### Archivos tocados

- `website.html`
- `website.css`
- `FAKI_WEB_PROGRESS.md`
- Capturas QA generadas:
  - `qa/evidentia-landing-desktop-v20-proof.png`
  - `qa/evidentia-landing-mobile-v38-proof.png`
  - `qa/evidentia-landing-mobile-v39-proof-clean.png`
  - `qa/evidentia-landing-mobile-v40-proof-safe.png`

### Referencias usadas

- Linear: producto vivo visible desde arriba, no explicacion abstracta.
- Rive: motion/proof como explicacion de estado, no decoracion.
- Claude Code / WorkOS patterns: control humano, permisos, trazabilidad y confianza como parte del producto.
- Vertical AI interno: negro premium, gradiente iridiscente y lenguaje visual propio de Miguel.

### Decisiones de diseño

- El primer CTA ya no suena a navegacion interna; suena a accion de producto.
- La prueba operativa aparece antes de la navegacion por paginas para que el visitante entienda rapido que se puede evaluar con material real.
- Mobile sacrifica algo de espectacularidad para ganar claridad, ancho seguro y lectura completa.
- Dental sigue como primer vertical, pero el hero mantiene la tesis grande: memoria contextual privada para equipos y organizaciones.

### Riesgos

- La landing ya tiene nivel de revision real, pero el salto final sigue siendo un microvideo autentico de uso de la app local: ingesta -> grafo -> chat RAG -> fuentes -> pack.
- Chrome headless genera avisos GPU no bloqueantes al tomar capturas; las capturas se escriben correctamente.
- La herramienta visual marco posible corte en una captura mobile, pero la medicion CDP final dio `documentElement.scrollWidth = 390`, `body.scrollWidth = 390` y cero nodos fuera del viewport.

### Verificacion

- Servidor local activo: `http://localhost:8791/website.html`.
- `curl -I` OK para `website.html` y `website.css`.
- Parser HTML OK con `html.parser`.
- Captura Chrome headless desktop: `qa/evidentia-landing-desktop-v20-proof.png`.
- Captura Chrome headless mobile final: `qa/evidentia-landing-mobile-v40-proof-safe.png`.
- Medicion Chrome DevTools Protocol mobile:
  - viewport: `390`
  - `documentElement.scrollWidth = 390`
  - `body.scrollWidth = 390`
  - ofensores fuera de viewport: `[]`
  - `.mobile-mini-mirror`: left `35`, right `355`, width `320`
  - `.hero`: height `656.8`

### Siguiente paso

1. Grabar microvideo real de producto local con flujo completo: subir fuente, indexar, ver grafo, preguntar, revisar fuentes y generar decision pack.
2. Sustituir parte del mock conceptual del hero por ese microvideo o integrarlo en `#video-producto`.
3. Hacer una pasada manual en navegador real de Safari/Chrome mobile si Miguel va a enseñarla en telefono.
4. Optimizar peso de video y preparar variante deploy/publicable si se va a subir.

### Estado

READY_FOR_MIGUEL_REVIEW - La web es usable y presentable para revision real. Para que quede brutal de verdad falta el microvideo real de uso de la app local y una ultima pasada de performance/assets antes de publicarla.

## 2026-06-27 - Evidence cockpit y mobile hero seguro

### Avances de hoy

- Converti el bloque Buyer-guided pilot demo en un cockpit de evidencia mas vendible:
  - cada fase del piloto cambia evidencias visibles, riesgo controlado, decision del comprador y entregable.
  - se refuerza la narrativa: input sensible -> mirror run -> QA gate -> decision comprable.
- Ajuste el hero mobile para priorizar claridad:
  - claim directo: Conocimiento interno. Respuestas auditables.
  - copy mas corto y orientado a fuentes, huecos y revision humana.
  - elimine del primer viewport movil los elementos que generaban riesgo de clipping; quedan para secciones posteriores.
  - CTA hero movil centrado y limitado para evitar overflow.
- Actualice cache-buster de CSS.

### Archivos tocados

- website.html
- website.css
- FAKI_WEB_PROGRESS.md
- Capturas QA generadas:
  - qa/evidentia-landing-desktop-v23-evidence-cockpit.png
  - qa/evidentia-landing-mobile-v49-safe-cta.png

### Referencias usadas

- Regard: datos dispersos -> insight/preparacion -> aprobacion humana -> output defendible.
- Momentic: QA gate antes de entregar; lo que falta tambien es parte del valor.
- Typeface: biblioteca de agentes/especialistas traducida aqui como fases y entregables por rol comprador.
- Linear: producto vivo y mecanismo visible, no promesa abstracta.
- Rive: motion/estado como explicacion del proceso, no decoracion.

### Decisiones de diseño

- El simulador deja de ser solo una explicacion por tabs y pasa a enseñar que compra el piloto: evidencia, riesgo, decision y entregable.
- Mobile queda menos espectacular pero mas seguro: el primer viewport debe leerse limpio en telefono antes que demostrar todos los efectos.
- El copy evita posicionamiento clinico: habla de conocimiento interno, respuestas auditables, fuentes y revision humana.
- Dental sigue como primer vertical en la narrativa general, pero el cockpit funciona para equipo, centro u organizacion.

### Riesgos

- La CSS movil tiene mucha defensa acumulada de iteraciones anteriores; se resolvio el clipping visible con una regla final segura, pero conviene hacer limpieza tecnica antes de publicar.
- El video hero sigue siendo asset propio/provisional; para publicacion publica falta compresion final y revisar audio/licencia en la variante con musica.
- Sigue faltando microvideo real de uso de la app local: subir fuente -> indexar -> grafo -> preguntar -> fuentes -> decision pack.

### Verificacion

- Servidor local usado: http://127.0.0.1:8793/website.html.
- curl -I OK para website.html y website.css.
- Parser HTML OK con html.parser.
- Sintaxis JS inline OK con new Function(script).
- Captura Chrome headless desktop: qa/evidentia-landing-desktop-v23-evidence-cockpit.png.
- Captura Chrome headless mobile final: qa/evidentia-landing-mobile-v49-safe-cta.png.
- Revision visual final de mobile: CTA hero no aparece cortado; estado aceptable para revision de Miguel.
- Chrome headless emitio avisos GPU/GCM no bloqueantes; las capturas se escribieron correctamente.

### Siguiente paso

1. Limpiar CSS movil acumulada para reducir reglas duplicadas y fragilidad.
2. Grabar microvideo real de producto local con flujo completo y sustituir parte del mock conceptual.
3. Comprimir videos y preparar variante publica ligera.
4. Hacer QA manual en Safari/Chrome mobile real antes de deploy externo.

### Estado

READY_FOR_MIGUEL_REVIEW - La landing esta presentable para Miguel y el mobile hero queda seguro. Para que quede brutal de verdad falta microvideo real de app local, limpieza CSS mobile y performance/assets antes de publicarla.
## 2026-06-26 - Video vectorial dental integrado

- Miguel aprobo la direccion visual del video de embeddings/mapa vectorial y pidio que las ventanas/documentos entraran mas rapido.
- Genere una v3 de 62 segundos con timing de ventanas acelerado, mapa vectorial dental, consulta semantica, respuesta trazable y musica del video de referencia para maqueta interna.
- Integre el video en website.html:
  - Hero: assets/evidentia/evidentia-vector-map-dental-v3-silent.mp4 en autoplay silencioso.
  - Seccion #video-producto: assets/evidentia/evidentia-vector-map-dental-v3-music.mp4 con controles y audio.
  - Poster: assets/evidentia/evidentia-vector-map-dental-v3-poster.jpg.
- Decision: para revision interna esta bien usar la musica de referencia; para publicacion comercial hay que sustituirla por musica licenciada o generada propia.
- Siguiente mejora Faki: comprimir variante web publica y crear version corta 12-18s para hero si el peso afecta carga movil.
- Extension aplicada despues: la app local tambien usa el video vectorial v3 en el hero y reemplaza el cubo simple por un canvas de mapa vectorial giratorio en hero/pipeline/mapa. Verificado con node --check app.js y carga local por curl -I.
- Ajuste solicitado por Miguel: no perder la imagen femenina original. Genere v4 del video con una escena de memoria humana/visual embedding usando reference-frame.jpg; web y app actualizadas a assets/evidentia/evidentia-vector-map-dental-v4-*. Verificado node --check app.js y curl -I para poster, silent mp4 y music mp4.
- Correccion posterior de UX app: Miguel detecto que el video v4 completo en el hero de la app quedaba apretado y con texto ilegible. Decision aplicada: primera pantalla de app vuelve a la chica original con cubo; el motion vectorial se mantiene en fondos/canvas de Mapa y pipeline, donde aporta sin perjudicar lectura. Web mantiene el video v4.

## 2026-06-26 - Vectoriales Evidentia v5 neutralizados

- Miguel pidió quitar rótulos dentales específicos del mapa vectorial: cerámica, CIELAB, CAD y similares.
- App: VECTOR_CLUSTERS queda en Conocimiento, Casos clinicos, Pacientes y Datos.
- Video: v5 regenerado con taxonomía general de Evidentia: conocimiento, casos clinicos, pacientes y datos. Se eliminaron referencias visibles a embedding dental, odontología, STL/CBCT, valor/croma/translucidez y decisión cerámica.
- Web: hero y sección Video apuntan a assets v5 finales con versión silenciosa y versión con música.
- QA: node --check OK; ffprobe OK 62s 1280x720 con audio AAC; revisión visual sin cerámica/CIELAB/CAD ni etiquetas dentales específicas.

## 2026-06-26 - App: RAG conectado a agentes/Projects y consentimiento

- Miguel detecto dos fallos de producto: no se entendia la conexion entre conocimiento RAG, agentes y Projects; y en la primera pantalla casi ningun boton parecia funcionar.
- App:
  - Hero actualizado con acciones reales: Nuevo registro, Ver mapa, Agentes / Projects y Consentimiento.
  - Las tarjetas Registros, Archivos y Consulta ahora son botones navegables.
  - Nuevo bloque RAG conectado: Conocimiento -> Vector RAG -> Agentes -> Projects -> Control/Consentimiento.
  - Mapa global visible aunque no haya caso activo: RAG conectado con Conocimiento, Casos clinicos, Pacientes, Datos, Agentes y Projects.
  - Pestaña Conectar reescrita como puente operativo para Pedro/Faki/Yolito, Claude Projects, ChatGPT Projects y automatizaciones internas.
  - Service worker actualizado a evidentia-shell-v30-agents-consent para evitar cache antiguo en movil.
- Proteccion de datos:
  - Consentimiento reforzado para datos de salud, imagen intra/extraoral, audio, video, PDF, transcripciones, RAG, agentes/Projects, IA externa, conservacion, derechos y revision humana.
  - Boton de descarga disponible desde home y desde la pestaña Permiso.
  - Plantilla fija creada: CONSENTIMIENTO_PACIENTE_EVIDENTIA.html.
- Verificacion:
  - node --check app.js OK.
  - http://127.0.0.1:8892/index.html, app.js, styles.css, sw.js, CONSENTIMIENTO_PACIENTE_EVIDENTIA.html responden OK.
  - /api/connectors/export responde OK en el servidor real Evidentia 8892; en servidor estatico 8888 es 404, pero la app usa fallback local para descargar bundle.
- Riesgo pendiente:
  - Falta QA visual real en navegador movil porque Playwright no esta instalado en este entorno. Hacer pasada manual en iPhone/Chrome antes de demo externa.
