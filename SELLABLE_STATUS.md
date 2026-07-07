# Evidentia Sellable Status

Fecha: 2026-07-07 08:36 Europe/Madrid

## Veredicto piguin

Evidentia sigue en estado **casi vendible, no vendible aun** como Evidentia Local Node: Vector Knowledge Mirror / memoria contextual local-first, fuentes visibles, datos bajo control del cliente, IA externa opcional y decision siempre humana.

La vuelta de hoy deja una mejora material verificable en el bloqueo de microdemo: `scripts/prepare_sellable_microvideo.sh` ahora valida el asset primario de video, su poster, duracion/resolucion con `ffprobe`, y genera un inventario de assets de venta junto al manifiesto tecnico. Tambien se ejecuto el gate real contra el nodo local y quedo evidencia nueva en `qa/microvideo/microvideo-ready-20260707T063120Z.md`.

Resultado real de hoy: **AMARILLO 12/14**. La demo tecnica esta viva, local, con fuentes y con video/asset primario trazable. No es VERDE porque falta candidato real, permiso explicito de Miguel y fecha de microdemo. Ademas, el asset primario validado dura 130.8s; sirve como prueba/asset de producto, pero todavia falta el microvideo final 60-90s aceptado por Miguel.

## Score De Vendibilidad

Total: 8.8/10

| Area | Score | Estado |
|---|---:|---|
| Web | 8.5/10 | Propuesta Local Node, video embebido y narrativa vendible. Falta QA visual final/captura nueva aceptada y microvideo final 60-90s. |
| App demo | 8.8/10 | Nodo local activo con 556 registros, 17.247 chunks compact vector, chat con 11 fuentes y modo rag-local sin IA externa probado hoy. |
| Producto | 8.5/10 | Tesis coherente: Vector Knowledge Mirror / memoria contextual local-first con fuentes. El gate ya comprueba resiliencia local y assets de video. |
| Venta | 8.5/10 | Oferta 500 EUR setup + 50 EUR/mes, gate comercial y pack de candidato listos. Falta candidato real, permiso y fecha. |
| Operacion | 8.8/10 | Script de microvideo endurecido con validacion de assets, endpoint, chat, bundle y modo local. Falta restore en equipo/carpeta final de cliente. |

## Estado Real Revisado

- Leidos `SELLABLE_LOOP.md` y `SELLABLE_STATUS.md`.
- Revisado estado real de repo, scripts, web, assets de video y gate comercial.
- Nodo local escuchando en `http://127.0.0.1:8892`.
- `/api/health`: OK, records=556.
- `/api/rag/stats`: OK, backend=compact_vector, chunks=17247, compactVectorChunks=17247, sqliteChunks=17247.
- `/api/ai/status`: OK, mode=rag-local, active=False.
- `/api/chat` con pregunta dental concreta: OK, sources=11.
- Asset primario validado: `assets/evidentia/evidentia-llm-ceramic-reference-v3.mp4`, 6.920.446 bytes, 130.8s, 848x384.
- Poster primario validado: `assets/evidentia/evidentia-llm-ceramic-reference-v3-poster.jpg`, 38.782 bytes.
- Bloqueo numero 1 detectado hoy: sigue faltando candidato comercial concreto con permiso explicito de Miguel y fecha de microdemo.

## Maximo 3 Acciones Elegidas Hoy

1. Endurecer el gate de microvideo para validar tambien assets de venta, no solo endpoints.
2. Ejecutar el gate real con pregunta dental concreta y modo local sin IA externa.
3. Actualizar estado vendible con evidencia nueva y sin maquillar el bloqueo comercial.

## Cambios Aplicados Hoy

- Editado `scripts/prepare_sellable_microvideo.sh`.
- Anadio variables `PRIMARY_VIDEO` y `PRIMARY_POSTER` para fijar el asset primario de venta.
- Anadio validacion de existencia/tamano de video y poster.
- Anadio lectura opcional con `ffprobe` de duracion y resolucion.
- Anadio `microvideo-assets-<stamp>.md` con inventario de MP4/JPG/GIF disponibles.
- Manifest de microvideo ahora enlaza asset primario, poster, duracion, resolucion e inventario.
- Generada evidencia nueva: `qa/microvideo/microvideo-ready-20260707T063120Z.md`.
- Generado inventario nuevo: `qa/microvideo/microvideo-assets-20260707T063120Z.md`.

## Verificacion Real

- `bash -n scripts/prepare_sellable_microvideo.sh`: PASS despues de corregir un escape en `find`.
- `curl http://127.0.0.1:8892/api/health`: PASS, records=556.
- `curl http://127.0.0.1:8892/api/ai/status`: PASS, mode=rag-local, active=false.
- `QUESTION='Que protocolo, decision o aprendizaje pierdes hoy entre fotos intraorales, PDF, audios y notas de laboratorio?' scripts/prepare_sellable_microvideo.sh`: PASS.
- Reporte generado con records=556, compactVectorChunks=17247, sqliteChunks=17247, sources=11, AI mode=rag-local, AI externa active=False.
- `ffprobe` sobre asset primario: PASS, duracion 130.8s, resolucion 848x384.
- Inventario generado con assets de video disponibles, incluyendo piezas de 62.0s en 1280x720 para posible microvideo final.

## Bloqueadores

1. Falta candidato comercial concreto: nombre, fecha de microdemo, forma de pago y permiso para piloto.
2. Falta aprobacion explicita de Miguel antes de enviar cualquier mensaje o hablar en su nombre.
3. Falta microvideo final 60-90 segundos aceptado por Miguel; hoy queda el asset primario y el inventario verificados, no el video final aprobado.
4. Falta preparar dos nodos separados para Doctor A / Doctor B o Candidato A / B en entorno limpio.
5. Falta repetir la restauracion en equipo externo real o carpeta final de cliente, fuera del repo de trabajo.

## Siguiente Accion

Cerrar el bloqueo comercial rellenando el `Bloque De Aprobacion Para Miguel` en `PEDRO_MICRODEMO_CANDIDATE_PACK_20260702.md` y ejecutar `scripts/microdemo_preflight_gate.sh` con `CANDIDATE_NAME`, `MIGUEL_APPROVAL=yes` y `DEMO_DATE`. Si Miguel no quiere elegir candidato aun, la siguiente vuelta debe producir el microvideo final 60-90s a partir de los assets ya inventariados y del manifiesto de hoy.

## Condicion De Salida

El loop no puede relajarse hasta que:

- Web >= 8/10 con QA visual final y microvideo real aceptado por Miguel.
- App demo >= 8/10 con flujo completo reproducido desde UI y documentado en video/capturas.
- Busqueda vectorial local compacta, backup restaurable y modo local sin IA externa explicados sin contradiccion comercial.
- Preflight de microdemo en VERDE con candidato real, permiso explicito de Miguel y fecha.
- Piloto fundador definido con candidato, precio, guion, objeciones y siguiente accion.
- Instalacion, backup y restauracion probados fuera del entorno de desarrollo.
- Miguel valide explicitamente que esta vendible.
