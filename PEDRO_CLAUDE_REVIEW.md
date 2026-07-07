# Pedro + Claude Evidentia Review

## Fecha

2026-07-07 11:30 Europe/Madrid

## Estado observado

- Evidentia sigue casi vendible, no vendible aun sin reservas para piloto fundador.
- Estado vivo: AMARILLO 12/14, con nodo local probado hoy temprano, 556 records, 17.247 chunks compact vector/SQLite, fuentes visibles y modo rag-local sin IA externa.
- Web/copy comercial ya estan avanzados por Faki; Pedro no duplica ese trabajo.
- Bloqueo comercial real: falta candidato concreto, permiso explicito de Miguel, fecha de microdemo y criterio de exito del candidato.
- Friccion de construccion detectada hoy: la app decia local-first y fuentes visibles, pero en el chat faltaba convertir esa promesa en prueba vendible inmediata para el fundador.

## Pregunta enviada a Claude

Se uso /Users/piguin/.openclaw/workspace/scripts/pekis_claude_bridge.py con esta pregunta breve:

> Actua como segundo criterio tecnico-producto para Evidentia, Vector Knowledge Mirror / memoria contextual local-first. Dental es primer vertical, pero no software medico ni diagnostico. Estado observado 2026-07-07: casi vendible; demo local viva con fuentes; bloqueo comercial: falta candidato real, permiso explicito de Miguel y fecha de microdemo. Ya existen discovery gate, microdemo gate y Decision Pack. App local muestra Local Node, fuentes visibles y modo sin salida externa. Enfocate en vender pilotos fundadores sin acciones externas. Responde breve en espanol: 1) debilidades reales de la app; 2) mejoras arquitectura/UX que aumenten vendibilidad; 3) riesgos tecnicos o posicionamiento; 4) maximo 3 acciones concretas ejecutables hoy.

## Resumen util de Claude

- Claude marco que "fuentes visibles" no basta si no son verificables y accionables desde la respuesta.
- Tambien marco que local-first debe poder comprobarse visualmente: salida externa, logs/prueba de aislamiento o bundle trazable.
- Recomendacion util: panel Trust/Proof visible, click-through o descarga de fuentes, y lenguaje claro de "no tengo evidencia suficiente" para no parecer software medico.
- Riesgo principal segun Claude: deriva a software medico si dental + memoria contextual se usa como decision automatica.

## Decision de Pedro

Pedro compra el diagnostico de Claude: el siguiente salto vendible no es otra promesa de Local Node, sino prueba visible dentro de la app. La mejora elegida es reforzar el panel del chat para que, en microdemo, Miguel pueda ensenar tres cosas sin explicar demasiado: sin salida externa activa, fuentes/chunks citables y descarga del knowledge bundle como prueba JSON.

## Mejora aplicada hoy

- Editado app.js: renderLocalFirstPanel ahora se llama "Prueba local-first", muestra "Sin salida externa activa" cuando no hay IA externa, cambia RAG a "Fuentes", explicita "decision humana, no clinica automatica" y anade CTA "Descargar prueba JSON" + "Ver trazabilidad".
- Editado styles.css: anadido .local-proof-actions para que esos CTAs queden compactos y legibles en el panel lateral del chat.
- No se tocaron acciones externas, clientes, emails ni promesas clinicas.

## Verificacion

- node --check app.js: PASS.
- rg -n "Prueba local-first|Descargar prueba JSON|local-proof-actions|Sin salida externa activa" app.js styles.css: PASS.
- git diff -- app.js styles.css revisado. Nota: el repo ya tenia muchos cambios previos sin commitear; Pedro solo trabajo sobre el panel local-first y su CSS, sin revertir trabajo ajeno.

## Impacto esperado en venta/piloto

En una microdemo, el fundador ya no tiene que creer "local-first" por copy. Lo ve en el mismo panel de chat y puede descargar un JSON trazable. Eso reduce objeciones de confianza, refuerza el precio fundador y baja el riesgo de venderlo como IA clinica.

## Bloqueo principal

Sigue faltando candidato real con nombre, relacion, permiso explicito de Miguel, fecha, 3 fuentes permitidas y responsable que valide valor. Sin eso, Pedro no debe contactar a nadie ni pedir piloto.

## Siguiente accion concreta

Proxima vuelta: hacer una prueba visual/manual del flujo Chat -> Descargar prueba JSON -> Ver trazabilidad, idealmente con captura o checklist, y despues cerrar candidato/fecha con el bloque de aprobacion de PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md cuando Miguel lo permita.
