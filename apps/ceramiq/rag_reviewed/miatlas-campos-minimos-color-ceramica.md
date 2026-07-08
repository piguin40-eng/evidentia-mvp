# MiAtlas: campos minimos para fichas de color ceramico

Estado: revisado operativo por self-improvement diario 2026-05-22.
Origen: reporte nocturno Yolito Ceram 2026-05-22 y criterio BigColor de integridad antes de RAG.
Ambito: fichas de masas, ceramicas, restauraciones, muestras cromaticas y reglas opticas usadas por Yolito Ceram, BigColor Ceram y MiAtlas.

## Regla central

Ningun item cromatico debe tratarse como conocimiento clinico-tecnico completo si no declara, o marca como desconocidos, sus metadatos criticos.

## Campos obligatorios

Cada ficha debe registrar:

- Material: feldespatica, disilicato de litio, zirconia, hibrida/resin-matrix, composite u otra familia.
- Marca y sistema: por ejemplo IPS e.max Ceram, Katana, Vita, GC, Kuraray Noritake o sistema propio.
- Masa o referencia comercial exacta.
- Familia optica: dentina, esmalte, opal, translucent, impulse, effect, stain, glaze, liner u otra.
- Zona dental: cervical, medio, incisal, mamelon, halo, proximal, mamelon interno, cuello o area especifica.
- Grosor o espesor aproximado usado para la observacion.
- Sustrato: natural, munon, disilicato, zirconia, metal, composite, fondo gris calibrado u otro.
- Cemento o medio optico si aplica.
- Condicion de iluminacion: D65, polarizada, flash, luz de laboratorio, UV u otra.
- Estado de envejecimiento: nuevo, cocido, glaseado, pulido, envejecido, termociclado o desconocido.
- Fuente: Miguel/laboratorio, IFU/ficha tecnica, paper, atlas interno, experiencia clinica o staging pendiente.
- Nivel de confianza: medido, estimado calibrado, estimado visual, candidato no validado.

## Campos extra para zirconia multilayer

Para zirconia multicapa, anadir:

- Grado: 3Y, 4Y, 5Y o mezcla si el fabricante lo declara.
- Capa del blank.
- Orientacion de nesting.
- Protocolo de sinterizado.
- Grosor final tras acabado.

## Campos extra para recetas ceramicas

Cuando la ficha alimente una receta por tercios, anadir:

- Tercio dental objetivo.
- Porcentaje de cada masa.
- Funcion optica de cada masa.
- Nota tecnica de aplicacion.
- Parametros de coccion solo si estan respaldados por IFU, ficha tecnica o RAG revisado.

## Politica RAG

- Las fichas incompletas pueden entrar en staging, pero no deben presentarse como regla clinica validada.
- Si falta calibracion, CIELAB y Delta E deben etiquetarse como estimados.
- Si falta fuente o sistema exacto, Yolito debe responder con limitacion explicita antes de recomendar material o receta.
- Para BigColor/MiAtlas, grosor, sustrato y material no son comentarios secundarios: son variables criticas de interpretacion optica.
