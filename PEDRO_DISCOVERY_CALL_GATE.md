# Evidentia - Puerta De Discovery Antes De Microdemo

Fecha: 2026-07-05
Owner: Pedro Sales

## Objetivo

Decidir en 15 minutos si un candidato merece microdemo de Evidentia o si primero hay que seguir descubriendo. Esta puerta evita vender una demo generica, protege el posicionamiento local-first y mantiene fuera cualquier promesa medica.

Evidentia se presenta como Vector Knowledge Mirror: memoria contextual privada, fuentes visibles, datos bajo control del cliente e IA externa opcional con proveedor/API del cliente.

## Regla De Uso

No pedir microdemo si esta puerta queda en rojo. Si queda en amarillo, pedir solo 3 fuentes de ejemplo y una pregunta real antes de agendar. Si queda en verde, pasar a `MICRODEMO_ACCEPTANCE_GATE.md`.

## Preguntas De Discovery

1. Que conocimiento valioso se pierde hoy entre WhatsApp, fotos, PDF, audios, notas, carpetas o memoria personal?
2. Que decision, protocolo, aprendizaje o criterio tarda demasiado en reconstruirse?
3. Que 3 fuentes concretas harian que una memoria con fuentes fuese util en 30 dias?
4. Quien puede validar si las fuentes recuperadas son correctas y utiles?
5. Que datos no deben entrar nunca en el piloto?
6. Puede empezar con datos ficticios, anonimizados o autorizados?
7. Quiere usar su propia API/proveedor de IA o prefiere empezar en modo local con fuentes?
8. Acepta que Evidentia no diagnostica, no prescribe y no decide?
9. Tiene sentido un piloto fundador de 30 dias con setup de 500 EUR y continuidad de 50 EUR/mes?

## Score De Discovery

| Bloque | 0 | 1 | 2 |
|---|---|---|---|
| Dolor | generico o curioso | dolor probable | perdida concreta de criterio/fuentes |
| Fuentes | no sabe | tipos de fuente claros | 3 fuentes concretas para probar |
| Permiso | ambiguo | usaria ficticios | ficticios/anonimizados/autorizados definidos |
| Validador | no existe | Miguel valida indirectamente | responsable del candidato valida valor |
| Limites | espera IA clinica | acepta limites verbalmente | repite que no diagnostica ni decide |
| Precio | evita precio | lo entiende pero duda | acepta rango fundador si ve valor |

## Interpretacion

- 10-12: verde. Preparar microdemo con permiso explicito de Miguel y pasar `MICRODEMO_ACCEPTANCE_GATE.md`.
- 7-9: amarillo. No pedir piloto todavia; pedir 3 fuentes y 1 pregunta real.
- 0-6: rojo. No vender. Usar la conversacion para aprender posicionamiento.

## No-Go Inmediato

Parar si el candidato pide diagnostico, recomendacion clinica automatica, promesa de resultado, uso de datos sensibles sin permiso, custodia cloud improvisada o que Helix pague la IA externa del cliente.

## Salida Minima

- Candidato:
- Dolor concreto:
- 3 fuentes:
- Datos permitidos:
- Validador:
- Modo IA: local con fuentes / API propia del cliente / pendiente
- Score:
- Decision: verde / amarillo / rojo
- Siguiente paso:

## Si Sale Verde

No saltar directamente a vender. Crear una copia de PEDRO_PILOT_DECISION_PACK_TEMPLATE.md para ese candidato y rellenar:

- dolor comprable;
- 3 fuentes permitidas;
- pregunta real de demo;
- validador;
- limites repetidos por el candidato;
- precio fundador y siguiente accion.

Si el Decision Pack queda incompleto, la salida correcta es amarillo aunque el score de discovery parezca alto.

## Frase Segura Si Encaja

> Si te encaja, la microdemo no intenta diagnosticar ni decidir. Solo probamos si tu propio conocimiento, con fuentes visibles y datos permitidos, se puede recuperar mejor en 30 dias.
