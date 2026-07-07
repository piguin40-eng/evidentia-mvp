# Evidentia - Roadmap de lanzamiento SEPES octubre 2026

Fecha: 2026-06-18
Contexto: Miguel quiere lanzar Evidentia a venta publica en SEPES en octubre. Hay julio, agosto y septiembre para pasar de MVP/demo a producto piloto vendible.

## Veredicto ejecutivo

Evidentia puede llegar a SEPES como producto vendible si el alcance se controla con disciplina.

No debe venderse como software medico, diagnostico clinico, IA dental validada ni plataforma cloud madura. Debe venderse como:

> Evidentia Local Node: una memoria vectorial privada para clinicas, laboratorios y equipos que quieren guardar conocimiento, casos, fotos, videos, audios, PDF, decisiones y protocolos en una base consultable con fuentes.

Objetivo realista para octubre:

- Vender pilotos pagados, no prometer una plataforma enterprise terminada.
- Tener instalacion local/hibrida demostrable.
- Tener demo dental impecable.
- Tener onboarding, precio, contrato, consentimiento, soporte y limites claros.
- Captar primeros clientes fundadores en SEPES.

## Producto que se puede vender en octubre

Nombre comercial recomendado:

- Evidentia Local Node
- Paquete: Piloto Fundador SEPES

Incluye:

- App local instalable en Mac/ordenador/servidor del cliente.
- Base local SQLite para registros, entidades, relaciones y evidencias.
- RAG local con Chroma.
- Upload de PDF, TXT, imagen, video y notas.
- Extraccion local basica de texto y analisis tecnico de imagen/video.
- Chat con conocimiento propio y fuentes.
- Busqueda semantica y busqueda local.
- Packs/export de evidencia operativa.
- Consentimiento y limites de uso.
- Demo dental preparada con casos anonimos/simulados.
- Soporte inicial y configuracion guiada.

No incluye en octubre:

- Diagnostico clinico autonomo.
- Multiusuario enterprise completo.
- Facturacion automatica.
- Cloud productivo general.
- Vision dental semantica validada.
- Garantia legal/regulatoria como producto sanitario.
- Integraciones completas con software clinico/laboratorio.

## Oferta SEPES

### Opcion recomendada

Piloto Fundador SEPES

Duracion: 30-60 dias.
Precio inicial recomendado: 900-1500 EUR setup.
Mensualidad posterior tentativa: 99-249 EUR/mes segun soporte, almacenamiento y alcance.

Incluye:

- Instalacion local.
- Carga inicial guiada de 30-100 piezas de conocimiento.
- Formacion de 60-90 minutos.
- Plantilla de consentimiento y limites.
- Revision semanal durante el piloto.
- Informe final: utilidad, fuentes recuperadas, busquedas evitadas, problemas detectados y decision de continuidad.

Condicion critica:

- Los primeros clientes deben aceptar que es piloto fundador, con limites claros y feedback obligatorio.
- Mejor vender menos clientes buenos que muchos compradores mal educados.

## Julio - Convertir MVP en producto instalable

Objetivo: que funcione de forma repetible fuera del ordenador de desarrollo.

P0 tecnico:

1. Congelar alcance v0.1.
2. Crear instalador/launcher serio para Mac.
3. Crear modo demo limpio con datos ficticios.
4. Crear modo cliente limpio con base vacia.
5. Asegurar persistencia local: SQLite, uploads, Chroma, exports y logs.
6. QA completo: crear registro, subir PDF/TXT/imagen/video, indexar, preguntar al chat, ver fuentes, exportar pack y reiniciar sin perder datos.
7. Controlar errores visibles: Chroma, ffmpeg, modelos/API y modo local limitado.
8. Crear backup/restauracion simple.

P0 producto:

1. Demo de 10 minutos perfecta.
2. Web/landing premium con CTA a piloto fundador.
3. Video corto de producto real, no solo estetica.
4. PDF comercial de una pagina.
5. Guia para Sergio/Miguel: como explicarlo sin prometer diagnostico.

Entregable de fin de julio:

- Evidentia v0.1 Local Node.
- Instalacion reproducible.
- Demo dental estable.
- Primer piloto interno o con clinico de confianza.

## Agosto - Pilotos controlados y endurecimiento

Objetivo: probar con 2-5 usuarios reales antes de vender en publico.

P0 pilotos:

1. Seleccionar 2-5 testers: laboratorio dental, clinica dental y profesional/formador con mucho conocimiento.
2. No meter datos sensibles identificables sin consentimiento.
3. Usar dataset anonimo o ficticio cuando sea posible.
4. Medir tiempo para guardar conocimiento, recuperacion correcta de fuentes, preguntas utiles, fallos de instalacion, fricciones y valor percibido.
5. Registrar feedback semanal.

P0 tecnico:

1. Mejorar ingestion: PDF robusto, TXT/Markdown, imagen/video metadata y audio transcrito si se integra Whisper local.
2. Mejorar RAG: fuentes citadas, confianza, respuesta cuando no sabe y cero invencion.
3. Mejorar UX: estado de indexacion, permisos, piloto y errores entendibles.
4. Crear sistema de actualizaciones manuales controladas.
5. Anadir export de datos del cliente.

P0 legal/comercial:

1. Revisar posicionamiento legal con abogado si se vende en contexto dental.
2. Preparar contrato piloto.
3. Preparar DPA/encargo de tratamiento si aplica.
4. Preparar consentimiento base.
5. Preparar disclaimer comercial: memoria/conocimiento, supervision humana, no diagnostico, no producto sanitario validado.

Entregable de fin de agosto:

- Evidentia v0.2.
- 2-5 pilotos con feedback.
- Documento de riesgos reales.
- Precio validado o ajustado.

## Septiembre - Preparacion SEPES

Objetivo: llegar a octubre con demo, oferta y operativa de venta cerradas.

P0 producto:

1. Cerrar v0.3 SEPES.
2. Grabar video demo final de 60-90 segundos.
3. Preparar demo offline por si falla internet.
4. Preparar laptop/iPad con app lista.
5. Crear dataset dental demo: caso estetico, protocolo laboratorio, seguimiento clinico, decision tecnica, PDF/protocolo y fotos/video anonimos o simulados.
6. Crear script de demo: problema, ingesta, mapa, pregunta, fuentes, valor, limites y oferta piloto.

P0 venta:

1. Landing final.
2. PDF comercial.
3. QR a lista de espera/piloto.
4. Formulario de lead.
5. Oferta SEPES: plazas limitadas, precio fundador y condiciones.
6. Preparar respuestas a objeciones: privacidad, instalacion, datos de pacientes, IA externa, precio, diferencia con ChatGPT/Drive/Notion y si es producto sanitario.
7. Definir seguimiento post-congreso: llamada 20 min, diagnostico de conocimiento, instalacion piloto y feedback semanal.

Entregable antes de SEPES:

- Demo estable.
- Oferta clara.
- Material comercial.
- Proceso de venta.
- Proceso de instalacion.
- Proceso de soporte.
- Limites legales listos.

## Riesgos principales

1. Venderlo como IA clinica. Mitigacion: lenguaje de memoria/conocimiento, no diagnostico.
2. Llegar con demo bonita pero producto fragil. Mitigacion: julio centrado en instalacion, persistencia, QA y errores.
3. Prometer cloud/multiusuario antes de tenerlo. Mitigacion: vender Local Node piloto, cloud como roadmap.
4. Usar datos sensibles sin marco legal. Mitigacion: pilotos con datos anonimos/ficticios o consentimiento claro.
5. Querer demasiadas features. Mitigacion: v0.1-v0.3 solo hace ingesta, RAG, fuentes, busqueda, pack y demo.
6. Que Sergio o Miguel vendan con claims distintos. Mitigacion: una hoja de posicionamiento unica y script de venta.

## Decision critica para Miguel y Sergio

Antes de seguir hay que decidir una de estas dos rutas:

### Ruta A - Piloto premium controlado

Vender 5-10 pilotos fundadores a 900-1500 EUR.

Ventaja: menos soporte, mas aprendizaje, clientes mejor filtrados.
Recomendacion: esta es la ruta correcta.

### Ruta B - Venta publica barata

Vender acceso amplio a bajo precio.

Riesgo: soporte, bugs, confusion legal, mala reputacion si falla.
No recomendado para octubre.

## Lo que hay que construir primero

Orden correcto:

1. Instalador/local node reproducible.
2. Dataset demo dental serio.
3. Flujo RAG con fuentes que no invente.
4. Estado de indexacion y errores.
5. Pack/export de valor.
6. Landing + video + PDF.
7. Contrato/consentimiento/disclaimer.
8. Pilotos reales.
9. Oferta SEPES.

No invertir todavia en:

- Pasarela de pago.
- Multiusuario complejo.
- App movil nativa.
- Cloud enterprise.
- Vision dental avanzada no validada.
- Automatizaciones clinicas agresivas.

## Mensaje corto para Sergio

Evidentia no debe salir en octubre como SaaS medico terminado. Debe salir como Piloto Fundador SEPES: un nodo local de memoria vectorial privada para clinicas/laboratorios/equipos, instalado en su entorno, que permite guardar conocimiento disperso y consultarlo con fuentes.

La prioridad de julio no es meter mas estetica: es que la instalacion, la demo, el RAG, las fuentes, el backup y los limites funcionen sin fallar.

## Proxima accion inmediata

Esta semana:

1. Crear rama/estado v0.1 producto.
2. Limpiar artefactos QA no necesarios.
3. Preparar dataset demo dental.
4. Ejecutar QA completo del flujo local.
5. Crear SALES_ONE_PAGER.md.
6. Crear DEMO_SCRIPT_SEPES.md.
7. Crear checklist de instalacion para cliente.
