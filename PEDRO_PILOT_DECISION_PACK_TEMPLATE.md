# Evidentia - Plantilla De Decision Pack Para Piloto Fundador

Fecha: 2026-07-06
Owner: Pedro Sales

## Objetivo

Convertir una discovery o microdemo de Evidentia en una decision concreta y defendible: piloto fundador, prueba previa con fuentes o no-go.

Este pack no vende software medico, diagnostico ni automatizacion clinica. Vende memoria contextual local-first con fuentes visibles, datos permitidos y decision humana.

## Como Usarlo

Rellenar una copia por candidato despues de PEDRO_DISCOVERY_CALL_GATE.md y antes de pedir un piloto pagado. Si falta permiso explicito de Miguel para contactar o hablar en su nombre, el pack queda en borrador interno.

## Resumen Del Candidato

    CANDIDATO:
    RELACION CON MIGUEL:
    TIPO: doctor / clinica / laboratorio / formador / equipo experto / otro
    RESPONSABLE QUE VALIDA VALOR:
    FECHA DISCOVERY:
    FECHA MICRODEMO PROPUESTA:
    PERMISO EXPLICITO DE MIGUEL: si / no
    FRASE APROBADA POR MIGUEL:

## Dolor Comprable

    CONOCIMIENTO QUE SE PIERDE HOY:
    DECISION, PROTOCOLO O APRENDIZAJE DIFICIL DE RECONSTRUIR:
    COSTE ACTUAL: tiempo perdido / dependencia de persona clave / error operativo / docencia pobre / otro
    POR QUE IMPORTA EN 30 DIAS:

## Fuentes Permitidas

No avanzar si las fuentes no son ficticias, anonimizadas o autorizadas.

| Fuente | Tipo | Estado de permiso | Por que demuestra valor |
|---|---|---|---|
| 1 |  | ficticia / anonimizada / autorizada |  |
| 2 |  | ficticia / anonimizada / autorizada |  |
| 3 |  | ficticia / anonimizada / autorizada |  |

Datos que no deben entrar nunca:

-

## Pregunta Real De Demo

La pregunta debe salir del dolor del candidato, no del guion generico.

    PREGUNTA:
    RESPUESTA ESPERADA COMO VALOR:
    FUENTES QUE DEBERIAN APARECER:
    CRITERIO DE EXITO EN 10 MINUTOS:

## Estado Tecnico Minimo

Marcar antes de pedir piloto:

- [ ] /api/health responde.
- [ ] Hay al menos 3 registros utiles o representativos.
- [ ] RAG/local retrieval devuelve fuentes visibles.
- [ ] scripts/pilot_readiness_snapshot.sh o scripts/microdemo_preflight_gate.sh genera PASS o AMARILLO explicado.
- [ ] IA externa esta desactivada o configurada con proveedor/API del cliente.
- [ ] Backup/restore tiene evidencia interna o limitacion explicada.

## Limites Que El Candidato Debe Repetir

Antes de cerrar piloto, el candidato debe entender estos limites:

- Evidentia no diagnostica.
- Evidentia no prescribe.
- Evidentia no decide por el profesional.
- Evidentia no procesa datos sensibles sin permiso, minimizacion y supervision.
- Evidentia recupera fuentes propias y prepara contexto para decision humana.

## Oferta Y Decision

    OFERTA PROPUESTA: Piloto fundador 30 dias
    SETUP: 500 EUR
    CONTINUIDAD: 50 EUR/mes soporte basico
    COSTE IA EXTERNA: cliente paga y controla su proveedor/API si decide usarla
    DECISION: piloto / prueba previa con 3 fuentes / no-go
    FECHA DE SIGUIENTE ACCION:

## Semaforo Pedro

- Verde: dolor concreto, 3 fuentes permitidas, validador, limites entendidos, precio aceptable si ve valor y prueba tecnica con fuentes.
- Amarillo: dolor probable, pero faltan fuentes, permiso, pregunta real, fecha o prueba tecnica del dia.
- Rojo: espera diagnostico, no hay permiso de datos, no hay validador, no acepta limites o solo quiere curiosidad sin piloto.

## Cierre Seguro

> Si en 30 dias Evidentia no recupera fuentes utiles ni reduce busqueda real, paramos. Si recupera contexto propio con fuentes visibles y ayuda a decidir mejor con supervision humana, entonces tenemos base para continuidad.
