# Corpus documental de PIA-3

Los documentos que tiene la planta y sobre los que se arma el RAG del TP: manuales de los
fabricantes, el manual de buenas prácticas de la operadora, dos años de órdenes de trabajo escritas
por la gente de campo y el contrato con la contratista. Todo es hipotético y coherente con el
simulador: mismos TAG, límites de alarma, códigos de repuesto, tareas y fallas.

No lo edites a mano: se genera con `planta/corpus` (ver al final).

## Qué hay

| Archivo | Documento | Páginas |
| --- | --- | --- |
| `manuales/TX350-D.md` / `.pdf` | Bomba triplex Trimax TX-350, manual de operación y mantenimiento, **Rev. D, vigente** desde 2023-03-15 | 44 |
| `manuales/TX350-C.md` / `.pdf` | El mismo manual, **Rev. C de 2019, reemplazada**. Sigue impresa en la sala de bombas | 44 |
| `manuales/FC48-3.md` / `.pdf` | Filtro de cartuchos Filtrapat FC-48, Rev. 3 | 42 |
| `manuales/MBP-4.md` / `.pdf` | Manual de buenas prácticas de operación y mantenimiento de la operadora, Rev. 4 | 42 |
| `contrato/CT-SVP-2025.md` / `.pdf` | Contrato de mantenimiento con Servipat: lista de precios y certificación | 8 |
| `contrato/CERT-EJ.md` / `.pdf` | Cierres de ejemplo de Servipat con sus diferencias y el monto del habilita | 10 |
| `contrato/cierres_ejemplo.json` | Los mismos cierres, estructurados | |
| `historial/ordenes.json` / `.csv` | Órdenes de trabajo de PIA-3 de octubre de 2024 a octubre de 2026 | |
| `evaluacion/retrieval.json` | Suite de preguntas con las secciones esperadas (recall@k) | |
| `evaluacion/historial_verdad.json` | Falla real de cada orden del historial, para evaluar | |
| `fragmentos.jsonl` | Una línea por sección de cada documento y por orden, con su cita y su texto | |
| `indice.json` | Metadatos de cada documento y de cada sección (cita, título, página del PDF) | |

## Cómo se cita

Cada sección tiene un número fijo y se cita como `<documento> §<número>`: `TX350-D §3.2` son los
límites de operación de la bomba en la revisión vigente, `MBP-4 §12.3` las reglas de aprobación.
Las órdenes se citan como `historial OT-25-0026`. Son las mismas citas que usa la suite de
retrieval y que tiene cada línea de `fragmentos.jsonl`.

## Lo que lo hace difícil a propósito

- **Versiones.** La Rev. C del manual de la bomba tiene otros límites (vibración 4,5 / 7,1 mm/s,
  aceite 85 / 95 °C), otro aceite (ISO VG 150), otros intervalos y los códigos de repuesto viejos
  (`350-EMP-03`). Los límites que valen son los de `datos/planta.yaml`, que repiten la Rev. D y el
  MBP-4. `indice.json` y `fragmentos.jsonl` dicen `"vigente": false` para la Rev. C.
- **Secciones que no aplican.** Otros modelos de la familia (TX-250, TX-500, FC-24, FC-96),
  opcionales que PIA-3 no tiene, instalación, preservación y las plantas PIA-1 y PIA-2.
- **Códigos distintos.** Los fabricantes usan sus propios códigos de falla (`TX-T07`, `FC-T02`).
  El MBP-4 §6 da la correspondencia con el catálogo de la planta (F01-F10).
- **Texto libre de campo.** Las órdenes tienen abreviaturas (`cbio`, `empaq`, `c/`, `x`), sin
  tildes, errores de tipeo y el código de falla sin cargar en casi la mitad.
- **El historial cambia la causa probable.** Hay fallas que se repiten en el mismo equipo y cuya
  causa de fondo no es la primera que da el manual: la vibración moderada de la B-101 que no se fue
  cambiando válvulas (era el acople), la empaquetadura de la B-103 que dura semanas (émbolo
  rayado), válvulas gastadas en dos bombas en pocos días (cartucho roto en el F-201B), la B-102 que
  cavita primero (filtro primario colmatado), transmisores clavados en invierno (líneas de impulso
  congeladas) y el consumo de aceite de la B-102 (retén del piñón).
- **Contrato.** El monto del habilita sale de la orden y de la lista de precios, no del cierre.
  Los cierres de ejemplo traen las mismas diferencias que el contratista virtual del simulador y
  otras: movilización mal cobrada, recargo de horas extra, lista de precios vieja.

## El historial y el simulador

El historial sigue la misma dinámica que el precalentamiento de cada escenario (fallas de bomba cada
3 a 9 días con F01 el doble de frecuente que F02, F04 y F05; cartuchos del primario cada unos 30
días y del secundario cada unos 45; inspección de válvulas después de un disparo) y termina el
2026-10-10, antes del arranque del escenario más temprano. `GET /api/historial-ordenes` devuelve
las órdenes del archivo anteriores al arranque del precalentamiento (`"origen": "archivo"`) seguidas
de las que genera el simulador (`"origen": "simulador"`).

## En la API de la planta

| Ruta | Qué devuelve |
| --- | --- |
| `GET /api/documentos` | La lista de documentos con sus metadatos y archivos |
| `GET /api/documentos/{id}` | Un documento con todas sus secciones (cita, título, página) |
| `GET /api/documentos/{id}/secciones?numero=3.2` | El texto de las secciones, o de una sola |
| `GET /api/historial-ordenes?equipo=&desde=&hasta=` | Archivo de dos años más el precalentamiento |
| `GET /documentos/{archivo}` | Los archivos de esta carpeta (`/documentos/manuales/TX350-D.pdf`) |

## Evaluar el retrieval

`evaluacion/retrieval.json` tiene 71 preguntas, escritas como las haría alguien de la planta, con
las secciones relevantes y, cuando hay trampa de versiones, las que no deberían aparecer:

```json
{"id": "lim-01", "pregunta": "¿A qué valor de vibración dispara por protección la bomba triplex?",
 "tipo": "limites", "relevantes": ["TX350-D §3.2", "TX350-D §6.1", "MBP-4 §5.1"],
 "distractores": ["TX350-C §3.2", "TX350-C §6.1"]}
```

```bash
cd planta
python -m corpus.evaluar --detalle
```

corre una línea de base BM25 sobre `fragmentos.jsonl` (hit@5 0,85, recall@5 0,66, la revisión
vieja antes que la vigente en una de cada diez preguntas). Para evaluar tu retriever, usá
`corpus.evaluar.evaluar(buscar, suite)` con una función que devuelva las citas recuperadas.

## Regenerar

```bash
cd planta
pip install -r corpus/requirements.txt
python -m corpus.generar --semilla 2026
```

Con la misma semilla y los mismos `datos/planta.yaml` y `datos/materiales.yaml` la salida es la
misma byte a byte. Al terminar corre `corpus.verificar`, que controla que límites, repuestos,
tareas, catálogo de fallas y citas de la suite sigan coherentes con la planta.
