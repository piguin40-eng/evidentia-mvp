# Evidentia Sellable Status

Fecha: 2026-06-29 08:31 Europe/Madrid

## Veredicto piguin

Evidentia sigue siendo vendible solo como **Evidentia Local Node** en demo tecnica controlada: memoria contextual local-first, fuentes visibles, datos bajo control del cliente, IA externa opcional con API propia y decision siempre humana.

La vuelta de hoy no maquilla un hallazgo importante: el nodo responde con 250 registros, 17.247 chunks SQLite, 6 fuentes en chat y bundle exportable, pero Chroma devuelve 0 chunks. Por tanto se puede ensenar como modo local con fallback SQLite y fuentes, no como RAG vectorial completo hasta reindexar/verificar Chroma.

## Score De Vendibilidad

Total: 8.0/10

| Area | Score | Estado |
|---|---:|---|
| Web | 8.4/10 | Propuesta Local Node, precio fundador y limites correctos. Falta QA visual final con captura nueva y microvideo real. |
| App demo | 8.1/10 | Nodo local activo con 250 registros, chat con 6 fuentes y knowledge bundle exportable. Chroma esta a 0; la demo depende de fallback SQLite local con fuentes. |
| Producto | 7.6/10 | Tesis coherente: Vector Knowledge Mirror / memoria contextual local-first con fuentes. Dental sigue como primer vertical, no limite. |
| Venta | 8.1/10 | Oferta 500 EUR setup + 50 EUR/mes ya alineada y hoy queda accion comercial concreta para elegir 2 candidatos y pedir microdemo. Falta nombre real y fecha. |
| Operacion | 6.9/10 | Scripts de readiness y microvideo pasan, ahora con advertencia comercial si Chroma esta vacio. Falta reindexar Chroma, instalacion externa/equipo limpio y backup restaurado fuera del entorno activo. |

## Estado Real Revisado

- Leidos SELLABLE_LOOP.md y SELLABLE_STATUS.md.
- Revisados SALES_ONE_PAGER.md, PILOT_LAUNCH_PLAN.md, FOUNDER_PILOT_ACCEPTANCE.md, scripts de microvideo/readiness y estado real de endpoints locales.
- curl /api/health: OK, records=250.
- curl /api/rag/stats: OK, chunks=0, sqliteChunks=17247.
- scripts/prepare_sellable_microvideo.sh: PASS, manifiesto nuevo generado.
- scripts/pilot_readiness_snapshot.sh: PASS, snapshot comercial nuevo generado.
- Bloqueo numero 1 detectado hoy: falta candidato comercial concreto con fecha de microdemo; bloqueo tecnico asociado: Chroma esta vacio y obliga a presentar la demo como fallback SQLite con fuentes.

## Acciones Hechas Hoy

- Endurecido scripts/pilot_readiness_snapshot.sh para que marque explicitamente el modo de recuperacion: Chroma vectorial, fallback SQLite local con fuentes, o no vendible.
- Endurecido scripts/pilot_readiness_snapshot.sh para anadir advertencia comercial cuando Chroma esta vacio aunque SQLite y fuentes permitan demo controlada.
- Endurecido scripts/prepare_sellable_microvideo.sh para que el manifiesto de grabacion indique Retrieval mode y avise que no debe decirse RAG vectorial completo si Chroma esta a 0.
- Creado PEDRO_COMMERCIAL_ACTION_20260629.md con candidato ideal, mensaje para pedir microdemo, preguntas de calificacion, cierre de piloto y limites de no-diagnostico.
- Generado manifiesto fresco de microvideo: qa/microvideo/microvideo-ready-20260629T063129Z.md.
- Generado snapshot fresco de readiness comercial: qa/pilot-readiness/pilot-readiness-20260629T063130Z.md.

## Verificacion Real

- bash -n scripts/prepare_sellable_microvideo.sh: PASS.
- bash -n scripts/pilot_readiness_snapshot.sh: PASS.
- bash scripts/prepare_sellable_microvideo.sh: PASS, genera manifiesto con Retrieval mode: fallback SQLite local con fuentes.
- bash scripts/pilot_readiness_snapshot.sh: PASS, genera snapshot con advertencia: Chroma esta vacio; no vender como RAG vectorial completo.
- curl -fsS http://127.0.0.1:8892/api/health: PASS, records=250.
- curl -fsS http://127.0.0.1:8892/api/rag/stats: PASS, chunks=0, sqliteChunks=17247.
- Lectura manual de PEDRO_COMMERCIAL_ACTION_20260629.md: contiene oferta 500/50, limites de no diagnostico y proxima accion comercial concreta.

## Bloqueadores

1. Falta candidato comercial concreto: nombre, fecha de microdemo, forma de pago y permiso para piloto.
2. Chroma devuelve 0 chunks; hay que reindexar o explicar sin ambiguedad que la demo actual usa fallback SQLite local con fuentes.
3. Falta microvideo real de 60-90 segundos usando el manifiesto generado.
4. Falta preparar dos nodos separados para Doctor A / Doctor B en entorno limpio.
5. Falta QA visual final de web/app tras la correccion de copy y precio.

## Maximo 3 Acciones De Mayor Impacto

1. Miguel elige hoy dos candidatos; Pedro envia el mensaje de PEDRO_COMMERCIAL_ACTION_20260629.md y pide microdemo de 10 minutos.
2. Reindexar Chroma o documentar procedimiento de recuperacion para que /api/rag/stats vuelva a mostrar chunks vectoriales antes de grabar el video final.
3. Grabar el microvideo real: web -> app -> pregunta -> fuentes -> bundle -> oferta 500/50, con aviso correcto si sigue en fallback SQLite.

## Siguiente Accion

Resolver Chroma a 0 o dejar prueba escrita de reindexado fallido; en paralelo, Miguel debe elegir dos nombres y Pedro debe pedir la primera microdemo con el mensaje preparado en PEDRO_COMMERCIAL_ACTION_20260629.md.

## Condicion De Salida

El loop no puede relajarse hasta que:

- Web >= 8/10 con QA visual final y microvideo real aceptado por Miguel.
- App demo >= 8/10 con flujo completo reproducido desde UI y documentado en video/capturas.
- Chroma o el modo de recuperacion local esten verificados y explicados sin contradiccion comercial.
- Piloto fundador definido con candidato, precio, guion, objeciones y siguiente accion.
- Instalacion, backup y restauracion probados fuera del entorno de desarrollo.
- Miguel valide explicitamente que esta vendible.
