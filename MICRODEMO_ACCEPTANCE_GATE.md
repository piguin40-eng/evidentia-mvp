# Evidentia - Puerta De Aceptacion De Microdemo

Fecha: 2026-07-02
Owner: Pedro Sales

## Objetivo

Evitar demos bonitas pero no vendibles. Antes de pedir o ejecutar una microdemo de 10 minutos, Pedro debe poder decir si Evidentia esta en verde, amarillo o rojo con pruebas concretas.

La puerta no valida software medico ni diagnostico. Solo valida si el piloto puede ensenarse como memoria contextual local-first con fuentes visibles, decision humana y datos autorizados.

## Semaforo

### Verde - Se Puede Pedir Piloto Fundador

Usar verde solo si todo esto esta cumplido:

- Candidato real identificado y Miguel aprobo contactar o hablar en su nombre.
- Datos de demo definidos como ficticios, anonimizados o autorizados.
- `scripts/pilot_readiness_snapshot.sh` termina en PASS el mismo dia.
- El nodo local responde `/api/health` con al menos 3 registros.
- `/api/rag/stats` muestra al menos 3 chunks recuperables en compact vector o SQLite.
- El chat devuelve al menos 1 fuente visible para una pregunta probada.
- El modo local sin IA externa responde con fuentes cuando `/api/ai/status` esta en `rag-local` y `active=false`.
- Pedro puede mostrar el knowledge bundle o pack sin explicar tecnologia de mas.
- El candidato entiende que Evidentia no diagnostica, no prescribe y no decide.
- Hay una decision concreta al final: piloto 30 dias / no-go / nueva prueba con datos.

### Amarillo - Demo Tecnica Controlada, No Cierre

Usar amarillo si el producto responde, pero falta una pieza comercial o de confianza:

- No hay candidato real o falta permiso explicito de Miguel.
- El microvideo real aun no existe.
- Hay fuentes, pero la pregunta de demo todavia no refleja dolor del candidato.
- El restore esta probado internamente, pero no en equipo/carpeta final de cliente.
- La recuperacion funciona por fallback SQLite y no por compact vector.
- La IA externa esta activa por configuracion del entorno y no se ha probado explicitamente el modo local sin API.

En amarillo se puede ensenar internamente o preparar material, pero no cerrar piloto pagado sin decir la limitacion.

### Rojo - No Ensenar Como Vendible

Parar la demo si ocurre cualquiera de estos puntos:

- El candidato pide diagnostico, recomendacion clinica automatica o promesa medica.
- No hay datos autorizados, anonimizados o ficticios adecuados.
- `/api/health` falla.
- El chat no devuelve fuentes.
- No se puede explicar donde viven los datos.
- No existe responsable que valide si una respuesta con fuentes es util.

## Pregunta De Prueba Minima

Antes de demo, probar una pregunta que no suene generica:

```text
Que conocimiento conecta estetica, laboratorio y aprendizaje?
```

Para un candidato real, reemplazarla por una pregunta de dolor concreto:

```text
Que protocolo, decision o aprendizaje pierdes hoy entre fotos, PDF, audios, WhatsApp o carpetas?
```

La respuesta vendible no es la mas larga. Es la que muestra fuentes revisables y deja claro que faltaria antes de convertirlo en protocolo.

## Score De Microdemo

Puntuar de 0 a 2 cada bloque:

| Bloque | 0 | 1 | 2 |
|---|---|---|---|
| Candidato | no existe | nombre posible | nombre + permiso + fecha |
| Datos | indefinidos | ficticios genericos | ficticios/anonimizados/autorizados para su dolor |
| Nodo | falla | responde parcialmente | health + RAG + chat con fuentes PASS |
| Valor | demo generica | caso de uso probable | pregunta real y criterio de exito |
| Confianza | limites flojos | limites dichos | datos, fuentes, backup y no diagnostico claros |
| Cierre | sin siguiente paso | interes verbal | piloto/no-go/revision fechada |
| Resiliencia local | no probado | responde con fuentes pero modo IA ambiguo | `rag-local`, `active=false` y fuentes visibles |

Interpretacion:

- 12-14 + candidato con permiso y fecha: verde, pedir decision de piloto fundador.
- 8-11: amarillo, demo controlada y resolver huecos.
- 0-7: rojo, no vender todavia.

## Frase De Cierre Segura

> Si en 30 dias Evidentia no recupera fuentes utiles ni reduce busqueda real, paramos. Si recupera contexto, detecta huecos y prepara mejores decisiones humanas, entonces sabemos que conocimiento merece convertirse en sistema.

## Checklist Antes De Llamar

- [ ] Miguel aprobo el contacto o la frase exacta.
- [ ] Candidato y responsable escritos.
- [ ] Datos permitidos definidos.
- [ ] Snapshot PASS generado hoy.
- [ ] Pregunta de demo probada y con fuentes.
- [ ] Limite no diagnostico preparado.
- [ ] Cierre de 30 dias preparado: 500 EUR setup + 50 EUR/mes.
- [ ] Si no encaja, criterio de no-go preparado.
