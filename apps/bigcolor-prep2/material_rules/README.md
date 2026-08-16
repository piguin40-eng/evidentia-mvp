# BigColor PREP 2 - reglas de material

Esta carpeta contiene reglas versionadas para que el visor traduzca una medicion de espesor por diente/zona en una accion tecnica de tallado controlado por color.

Principios:

- Los espesores con fuente primaria se marcan como `verified`.
- Los datos de fuentes secundarias o guias copiadas se marcan como `secondary_unconfirmed`.
- Los rangos historicos de demo se conservan como `estimated_legacy_demo`, no como recomendacion clinica.
- Cuando no hay IFU/ficha tecnica localizada, el material queda como `pending_source`.
- La salida es de planificacion tecnica/laboratorio. No diagnostica, no sustituye IFU, criterio clinico ni validacion de registro/geometria.

Archivo activo:

- `material_rules_2026-08-16.json`

Fixture auxiliar activo:

- `viewer_exported_missing_rule_fixture_2026-08-10.json`: fixture exportable CSV/visor para demostrar que una fila sin cruce exacto `material_key + profile_key + zone_key` queda gris, con requerido pendiente y deficit clinico nulo. No anade espesores clinicos nuevos.

Versiones:

- `material_rules_2026-07-02.json`: IPS e.max Press con minimos primarios desde pagina Ivoclar y stubs pendientes.
- `material_rules_2026-07-03.json`: anade IPS e.max CAD desde guia oficial Ivoclar/CEREC 2015, con caveat obligatorio de confirmar eIFU/IFU vigente.
- `material_rules_2026-07-04.json`: identifica IPS Empress CAD con fuentes primarias Ivoclar revisadas, pero mantiene espesores por zona como `pending_source` porque no se localizo tabla IFU/ficha tecnica de preparacion.
- `material_rules_2026-07-05.json`: anade protocolo codificable para materiales pendientes y bloquea AMT con zonas cervical/medio/incisal en gris hasta tener producto exacto e IFU/ficha tecnica.
- `material_rules_2026-07-06.json`: anade matriz codificable de accion por fila para IPS e.max CAD veneer y materiales pendientes; no anade espesores clinicos nuevos.
- `material_rules_2026-07-07.json`: anade guia codificable para IPS e.max Press y marca explicitamente cuando un minimo global verificado se esta mapeando a zonas del visor; el candidato incisal 0.4 mm sigue secundario/no activo.
- `material_rules_2026-07-08.json`: anade perfil candidato secundario para IPS Empress CAD veneer (0.6 cervical, 0.7 labial/medio, 1.0 incisal si incluye borde incisal) desde copia no primaria; el perfil activo por defecto sigue `pending_source`/gris hasta localizar IFU/ficha tecnica vigente de Ivoclar.
- `material_rules_2026-07-10.json`: re-audita IPS e.max Press en pagina primaria Ivoclar y mantiene minimos globales verificados con caveat explicito de que no son tabla IFU por zona; anade ejemplos codificables diente-zona-medido-requerido-accion para veneer, onlay/occlusal veneer y corona.
- `material_rules_2026-07-11.json`: re-audita la pagina actual de IPS e.max CAD; confirma identidad/indicaciones generales pero no tabla numerica de espesor, mantiene las reglas numericas solo como guia Ivoclar/CEREC 2015 con eIFU vigente pendiente y anade ejemplos codificables por fila para veneer y corona posterior.
- `material_rules_2026-07-12.json`: anade contrato de validacion por fila para el visor: separa reglas verificadas/primarias, candidatas secundarias, pendientes de fuente y demo; no incorpora espesores clinicos nuevos.
- `material_rules_2026-07-13.json`: re-audita IPS Empress CAD en pagina primaria actual de Ivoclar; confirma identidad/material y que el espesor minimo depende del tipo de restauracion y debe consultarse en IFU, pero no anade numeros verificados. El perfil activo sigue `pending_source`/gris y el candidato secundario sigue inactivo.
- `material_rules_2026-07-14.json`: archiva una guia primaria Ivoclar de preparacion IPS Empress Esthetic como guardrail de no extrapolacion. No valida espesores IPS Empress CAD; el perfil activo CAD sigue `pending_source`/gris hasta localizar IFU/ficha tecnica CAD vigente.
- `material_rules_2026-07-15.json`: anade triage de fuente para IPS Empress CAD y AMT. No localiza IFU/ficha tecnica primaria nueva, por lo que Empress CAD sigue gris/pending_source y AMT sigue bloqueado por identidad de producto.
- `material_rules_2026-07-16.json`: re-audita la pagina actual de IPS e.max CAD; confirma identidad/familia/indicaciones generales, pero no localiza eIFU/IFU vigente con tabla numerica nueva. Mantiene los espesores de IPS e.max CAD atados a la guia Ivoclar/CEREC 2015 con caveat visible y ejemplos codificables de fila.
- `material_rules_2026-07-17.json`: convierte los minimos globales verificados de IPS e.max Press en una matriz explicita de seleccion para el visor: veneer fino 0.3 mm, corona 1.0 mm y onlay/occlusal veneer 1.0 mm, siempre con caveat de que no son tabla IFU por zona. No anade espesores nuevos.
- `material_rules_2026-07-18.json`: re-audita IPS Empress CAD en pagina primaria Ivoclar y cierra el comportamiento de visor cuando la IFU esta pendiente: identidad/familia verificadas, espesores numericos no verificados, salida gris por defecto y candidato secundario conservado solo como QA no activo.
- `material_rules_2026-07-19.json`: re-audita AMT como identificador pendiente. No localiza producto/fabricante/IFU trazable, asi que convierte AMT en contrato de intake codificable: required_mm nulo, salida gris/low_confidence y campos obligatorios para desbloquear espesores.
- `material_rules_2026-07-21.json`: anade matriz codificable de preparacion por material/perfil: IPS e.max Press puede colorear con minimo global y caveat; IPS e.max CAD puede colorear con guia Ivoclar/CEREC 2015 y caveat de eIFU vigente; IPS Empress CAD y AMT quedan gris/bloqueados salvo candidato secundario inactivo.
- `material_rules_2026-07-22.json`: anade contrato de display para selector del visor con etiqueta, badge, permiso de color y razon de bloqueo/caveat por perfil. No anade espesores clinicos nuevos.
- `material_rules_2026-07-23.json`: anade contrato codificable de accion por fila diente-zona-medido-requerido para que el visor traduzca material/fuente/medicion en color y accion tecnica. No anade espesores clinicos nuevos.
- `material_rules_2026-07-24.json`: anade contrato de frases por zona/material para salida visible estable: diente, zona, espesor medido, espesor requerido y accion tecnica. No anade espesores clinicos nuevos.
- `material_rules_2026-07-25.json`: anade matriz plana de espesor requerido por material/perfil/zona y crosswalk de zonas visibles del visor. Separa permiso de color, fuente/caveat y estado pendiente sin anadir espesores clinicos nuevos.
- `material_rules_2026-07-26.json`: anade resolutor codificable por fila para convertir diente/zona/material/perfil/espesor medido/QA en color, deficit y accion tecnica. No anade espesores clinicos nuevos.
- `material_rules_2026-07-27.json`: anade contrato de lectura tecnica por zona/material para salida visible estable: diente, zona, medido, requerido, deficit, color, accion, fuente y caveat. No anade espesores clinicos nuevos.
- `material_rules_2026-07-28.json`: anade contrato RAG por fila para ordenar QA geometrico, fuente/trazabilidad, deficit tecnico, color y accion de tallado. No anade espesores clinicos nuevos.
- `material_rules_2026-07-29.json`: anade matriz plana codificable material/perfil/zona para que el visor resuelva requerido, evidencia, permiso de color y accion tecnica por fila. No anade espesores clinicos nuevos.
- `material_rules_2026-07-30.json`: anade contrato de handoff de fuente/trazabilidad por fila para que el visor separe verificado, candidato secundario, demo y pendiente antes de resolver color. No anade espesores clinicos nuevos.
- `material_rules_2026-07-31.json`: anade compuerta codificable de decision por fila: QA geometrico primero, fuente pendiente/secundaria bloquea color, demo separado, y solo reglas verificadas/primarias archivadas calculan deficit/RAG con caveat visible. No anade espesores clinicos nuevos.
- `material_rules_2026-08-01.json`: anade contrato visible/exportable por fila para que el visor muestre diente, zona, medido, requerido, deficit, decision, color, accion, fuente y caveat de forma estable. No anade espesores clinicos nuevos.
- `material_rules_2026-08-02.json`: anade matriz de accion tecnica por umbral de deficit para filas que ya pasaron QA/fuente: gris si bloqueada, rojo por deficit, amarillo limite, verde cumple y morado exceso cuando exista limite. No anade espesores clinicos nuevos.
- `material_rules_2026-08-03.json`: anade fixture codificable de resolucion por fila para validar salida diente/zona/medido/requerido/deficit/color/accion/fuente/caveat en casos rojo, amarillo, verde y gris. No anade espesores clinicos nuevos.
- `material_rules_2026-08-04.json`: anade matriz codificable de permiso/bloqueo por fuente (`color_permission`) para que el visor permita RAG solo con caveat visible en perfiles verificados/archivados y fuerce gris en IPS Empress CAD/AMT pendientes. No anade espesores clinicos nuevos.
- `material_rules_2026-08-05.json`: anade contrato de trazabilidad por fila (`source_trace_status_es`/`source_trace_token`) para que el visor explique si una fila puede calcular RAG con caveat o debe quedar gris por fuente pendiente, candidato secundario o material no identificado. No anade espesores clinicos nuevos.
- `material_rules_2026-08-06.json`: anade contrato de frase tecnica final por fila (`viewer_sentence_es`) para que el visor/export entregue diente, zona, medido, requerido, fuente/color y accion tecnica sin activar pendientes como reglas clinicas. No anade espesores clinicos nuevos.
- `material_rules_2026-08-07.json`: anade contrato material-zona por fila para resolver diente, zona, espesor medido, espesor requerido, deficit/color permitido y accion tecnica con precedencia explicita de QA/fuente. No anade espesores clinicos nuevos.
- `material_rules_2026-08-08.json`: anade contrato de join estricto `material_key + profile_key + zone_key`; si falta cruce exacto el visor debe bloquear gris sin requerido numerico ni deficit clinico. No anade espesores clinicos nuevos.
- `material_rules_2026-08-09.json`: anade fixture codificable para `blocked_missing_material_zone_rule` con tres casos negativos de zona/perfil/material ausente. No anade espesores clinicos nuevos.
- `viewer_exported_missing_rule_fixture_2026-08-10.json`: convierte el bloqueo por regla ausente en filas CSV exportables para validar diente, zona, medido, requerido pendiente, deficit nulo, color gris, accion tecnica y caveat. No anade espesores clinicos nuevos.
- `material_rules_2026-08-11.json`: anade contrato QA exportable para conectar la fixture CSV/visor de `blocked_missing_material_zone_rule` al smoke de reglas activas. No anade espesores clinicos nuevos.
- `material_rules_2026-08-12.json`: anade contrato de salida por fila para fuentes pendientes: diente/zona/medido visibles, requerido pendiente, color gris y deficit clinico nulo para IPS Empress CAD, candidato secundario Empress y AMT. No anade espesores clinicos nuevos.
- `material_rules_2026-08-13.json`: anade contrato final de salida diente-zona-material con precedencia QA geometrico -> join material/perfil/zona -> fuente/requerido -> RAG permitido. No anade espesores clinicos nuevos.
- `material_rules_2026-08-14.json`: anade contrato de banda de accion tecnica por fila para exportar `action_band_key`, requerido, deficit, color, accion, fuente y caveat con prioridad QA/join/fuente antes de RAG. No anade espesores clinicos nuevos.
- `material_rules_2026-08-15.json`: anade contrato de compatibilidad exportable entre `Action band key` canonico y `Legacy action band key` historico; normaliza alias sin desbloquear RAG ni anadir espesores clinicos nuevos.
- `material_rules_2026-08-16.json`: anade contrato canonico de fila diente-zona-material para exportar espesor medido, requerido, estado de fuente, deficit, color, accion tecnica y caveat; separa verificado/legacy/pending/secondary sin anadir espesores clinicos nuevos.

Campos pensados para el visor:

- `material_key`: identificador estable para UI/API.
- `restoration_type`: veneer, crown, onlay, etc.
- `zones[].zone_key`: zona usada por el motor actual o futuro.
- `zones[].required_mm`: minimo, ideal y limite cuando exista fuente suficiente.
- `zones[].evidence_status`: estado de trazabilidad.
- `measurement_output_contract`: columnas minimas para tabla/export.
- `color_policy`: traduccion de diferencia medida-requerida a color y accion tecnica.
