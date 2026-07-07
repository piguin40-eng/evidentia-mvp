# Evidentia - QA demo reproducible

Objetivo: validar que Evidentia puede ensenarse como piloto local-first sin depender de promesas.

## Puerta de inicio

- Usar solo datos ficticios, anonimos o autorizados.
- Confirmar que la app no se presenta como diagnostico clinico ni software medico.
- Hacer copia de seguridad de `data/` antes de la demo si contiene material real.
- Confirmar `/api/health`, `/api/rag/stats` y `/api/ai/status` antes de empezar.
- Si se graba microvideo o pieza comercial, usar solo audio propio, licenciado o generado para Evidentia. La musica extraida de videos de referencia sirve solo para maqueta interna y debe sustituirse antes de publicar, enviar como demo comercial o incrustar en web publica.
- Si la demo usa acceso movil/PWA, no registrar claves reales en runbooks, memoria, capturas ni reportes. Probar login correcto/incorrecto y registrar solo PASS/BLOCKED, modo de auth y URL temporal.
- Las URLs `trycloudflare.com` son validas solo para prueba interna. No cuentan como despliegue comercial ni como app de mercado estable.

## Flujo P0

1. Abrir la app desde el launcher o servidor local.
2. Crear un registro demo con titulo, notas y contexto suficientes.
3. Subir al menos:
   - un TXT o Markdown,
   - un PDF,
   - una imagen,
   - un audio o video corto propio/autorizado.
4. Guardar el registro.
5. Verificar que el registro aparece en busqueda local.
6. Abrir Chat y preguntar por contenido que este dentro del registro.
7. Comprobar que la respuesta cita fuentes o registros recuperables.
8. Abrir Intel y revisar ROI, contradicciones, riesgos o conexiones.
9. Abrir permisos/consentimiento y confirmar limites visibles.
10. Exportar pack o informe y abrir el archivo generado.
11. Reiniciar servidor/app y confirmar que el registro, busqueda y RAG siguen disponibles.

## Puerta RAG

- Si una respuesta no tiene fuente clara, no cuenta como prueba valida.
- Si el audio/video se transcribe mal, marcarlo como riesgo y no indexarlo como conocimiento fiable sin revision.
- Si se usa IA externa, confirmar que el estado de proveedor y consentimiento estan claros.

## Resultado esperado

La demo cuenta como pasada solo si Miguel puede repetir el flujo en 10 minutos, explicar valor y limites sin improvisar, y recuperar conocimiento con fuentes despues de reiniciar.

## Salida del run

Registrar en `SELLABLE_STATUS.md`:

- fecha/hora,
- datos usados,
- pasos pasados/fallidos,
- capturas o artefactos generados,
- licencia/origen del audio si hay video,
- modo de auth movil y resultado de login si se usa PWA,
- bloqueador principal,
- siguiente accion.
