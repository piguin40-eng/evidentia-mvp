# Evidentia - guia de prueba para piloto de conocimiento

## Objetivo de esta prueba

Probar si Evidentia sirve para que una persona, equipo o centro guarde conocimiento real sin tener que aprender una herramienta compleja:

- notas,
- transcripciones,
- fotografias,
- videos,
- PDF,
- escaneos o archivos tecnicos,
- decisiones,
- dudas,
- seguimiento,
- aprendizajes propios.

## Como presentarlo

Frase recomendada:

> Evidentia es un nodo local para convertir conocimiento, archivos, decisiones, conversaciones, fotos, videos, PDF, audios transcritos y notas en una base vectorial propia, consultable con fuentes.

No presentarlo como diagnostico clinico ni como software medico terminado. Es un piloto funcional para validar memoria, recuperacion y trazabilidad del conocimiento propio. Dental puede ser el primer vertical, pero la tesis del producto es memoria vectorial privada para equipos.

## Arranque local

1. Abrir la carpeta `evidentia-mvp`.
2. Doble clic en `start_evidentia.command`.
3. Abrir en el navegador:

`http://127.0.0.1:8892`

## Antes de meter datos reales

No introducir datos identificables o sensibles sin permiso/consentimiento firmado.

Usar la pestaña **Permiso** para generar el documento base cuando aplique.

Para una demo comercial inicial, usar solo registros ficticios o anonimizados. Si la base contiene registros de prueba anteriores, preparar una copia limpia antes de compartir pantalla o ceder acceso.

## Donde se guardan los datos

- Base estructurada: `data/evidentia.sqlite`
- Archivos subidos: `data/uploads/`
- Indice vectorial compacto local: `data/rag/vector/`
- Espejo recuperable de chunks: tabla `rag_chunks` en `data/evidentia.sqlite`
- Exportaciones: `data/exports/`
- Auditoria: `data/audit/`

## Prueba recomendada

1. Crear un registro no identificable o con permiso firmado.
2. Pegar una transcripcion o explicacion libre de lo que hizo el usuario o equipo.
3. Subir 2-3 fotos, un PDF, un video corto o una nota.
4. Registrar si fue exito, fracaso, duda o aprendizaje.
5. Guardar en el mapa. En ese momento Evidentia indexa notas y texto extraible en el RAG local con fuentes.
6. Entrar en **Chat** y preguntar por algo que el usuario o equipo haya guardado.
7. Revisar si la respuesta cita fuentes/registros utiles.
8. Buscar despues por palabras normales, como lo preguntaria una persona del equipo.
9. Anotar que friccion impide usarlo cada semana.

## Criterio de exito

La prueba funciona si el usuario entiende en menos de 5 minutos:

- donde volcar su conocimiento,
- que se guarda,
- donde queda guardado,
- como hablar con su mapa de datos,
- como buscarlo despues,
- y que los permisos protegen a las personas, al centro y al conocimiento privado cuando haya datos sensibles.

## Limites que hay que decir en voz alta

- No sustituye criterio humano.
- No emite diagnostico validado.
- La vision de imagen/video actual es tecnica y local; todavia no interpreta semantica avanzada del dominio.
- La transcripcion automatica integrada y OCR robusto son siguientes pasos.
- El valor del piloto es ordenar, consultar y no perder conocimiento propio.
