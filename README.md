# Evidentia Curso — conocimiento cero

Paquete independiente. No incluye datos, documentos, embeddings, backups ni credenciales de Miguel. No copiar ningún directorio de otra Evidentia.

## Arranque

1. Python 3.11+; instalar `app/requirements.txt` para funciones de documentos y vectores.
2. Configurar las credenciales independientes del adjunto privado: `EVIDENTIA_BASIC_AUTH_USER` y `EVIDENTIA_BASIC_AUTH_PASSWORD`.
3. Definir `COURSE_DATA_DIR` como un volumen NUEVO y vacío, persistente durante todo el curso. No apuntarlo al volumen de Miguel. El arranque rechaza carpetas no vacías sin marca del curso.
4. `cd app && python3 start_course.py`. Puerto en `PORT` (8898 por defecto). Publicar únicamente tras proxy HTTPS.
5. Gateway: HTTP Basic en servidor, validando previamente los permisos del alumno en WordPress. No enviar credenciales al navegador si se utiliza gateway.

Disponible para pruebas técnicas desde el despliegue; fin de acceso predeterminado 23/11/2026 a las 23:59:59 Madrid. El mes lectivo es 23/10–23/11. Configurable mediante `COURSE_ACCESS_END` ISO con zona horaria. Sin pagos automáticos ni API de IA externa activada.

El acceso de esta versión es COMPARTIDO: todos los alumnos de la misma instancia ven los datos que incorporen. Solo prácticas ficticias. Para cuadernos privados, desplegar una instancia y un volumen independientes por alumno. Conocimiento cero describe el estado inicial, no implica aislamiento multiusuario.

La recuperación local empieza sin fuentes y necesita que los alumnos incorporen material. Exportar los resultados antes de que caduque el acceso. Este ZIP no acredita que una URL de Render esté desplegada ni verificada.
