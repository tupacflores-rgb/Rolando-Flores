# Planta de inyección de agua

Sistema para la Entrega 1 del TP: parte de recorrida por voz, detección en
planta, órdenes de trabajo con evidencia, tools de solo lectura, servidor MCP
y RAG con metadatos por equipo.

## Ejecución

Requiere Python 3.11+ y Docker Compose:

```powershell
docker network create planta-lan
docker compose up --build
```

La API queda en `http://localhost:8000`; la documentación OpenAPI está en
`/docs` y el healthcheck en `/health`. El contenedor arranca sin depender de
`context/` (directorio ignorado por Git): copia solo `app/`, `scripts/` y
`pyproject.toml`, e instala el contrato desde Git con una revisión fija.

Para ejecutar las pruebas localmente:

```powershell
python -m pip install -e ".[test]"
python -m pip install "git+https://github.com/NovitSoftware/academia2026-tp.git@ab65b95e911731351dba395817a74a8cc60da2b2#subdirectory=contrato"
pytest
```

## Qué corre en la planta y qué en la nube

Todo lo crítico corre en la PC de planta (`academia.planta: pc`):

- **Parte por voz**: transcribe con un modelo local (faster-whisper-small con
  revisión fija) y extrae filas estructuradas con un extractor determinista.
- **Detección**: límites de `planta.yaml`, anomalía sostenida para sensores y
  alertas de seguridad S1-S4 locales, sin nube.
- **Cola offline**: lo que sale de la planta queda en cola idempotente y se
  sincroniza cuando vuelve el enlace.
- **Reglas de aprobación**: en código, deterministas y auditadas.

Los manuales, el historial y el contrato se consultan por API/SQL o RAG; el RAG
actual es un índice léxico BM25 (fallback determinista) y pgvector es el backend
previsto.

## Integración con la planta

La API se conecta al broker MQTT cuando `MQTT_HOST` está definido. Consume
`planta/sensores/#`, `planta/recorridas`, `planta/cierres` y
`planta/respuestas`, y publica `sistema/eventos`, `sistema/ordenes`,
`sistema/tablet` y `sistema/estado` (latido cada 30 s). Al arrancar carga
equipos y límites desde `PLANTA_URL/api/planta` (o `datos/planta.yaml`).

```powershell
$env:MQTT_HOST = "broker"
$env:PLANTA_URL = "http://sim:8100"
```

## Parte por voz

`app/integrations.py` convierte una transcripción en `FilaParte` (una fila por
equipo y variable) con:

- resolución de nombres informales ("la dos", "el filtro B", "la de reserva")
  contra `planta.yaml`;
- inferencia de variable (descarga, diferencial, temperatura de aceite o
  rodamiento, vibración, succión, nivel) desde la frase y el equipo;
- unidad del manómetro local por equipo, con normalización de `kilos`,
  `kg/cm²`, `kgf/cm2`, `psi`, `bar`;
- números en palabras ("ciento doce", "mil seiscientos cuarenta", "uno coma
  ocho", "uno ocho");
- pregunta ante ambigüedad: "la bomba" a secas, o un diferencial dicho
  "dieciocho" en lugar de "uno ocho".

El borrador se publica en `sistema/tablet`; el operador confirma o corrige
("No, la uno estaba en ciento quince kilos") y el parte pasa de `Borrador` a
`Confirmado`, que es cuando se evalúan eventos y alertas.

## Detección y órdenes

- `POST /api/sensores` y el canal MQTT evalúan lecturas contra los límites del
  sensor; una anomalía sostenida escala y una condición insegura (agua a
  presión, olor a gas, humo/fuego, persona lesionada) genera `AlertaSeguridad`
  y un aviso en la tablet en menos de 30 s, sin enlace ni nube.
- La orden se genera con la tarea del catálogo, repuestos, costo y evidencia.
  Se aprueba sola solo si la tarea es estándar, mantiene la inyección (la
  reserva está realmente disponible), hay stock, el costo es menor a USD 2.500
  y el trabajo es propio. Cualquier excepción queda pendiente con motivo.

## Cierre por voz

`planta/cierres` se transcribe localmente, se extraen tareas, repuestos, horas
y prueba final, y se comparan contra la orden. Una diferencia pasa la orden a
`Observada` con el motivo; si el audio no trae evidencia interpretable, la
orden no se cierra.

## Tools, MCP y RAG

Las tools de solo lectura (equipos, historial de sensores, historial de
órdenes, inventario, materiales, tareas, manuales) validan con Pydantic
`extra="forbid"` y registran cada llamada en `service.tool_audits`. El
historial de sensores y órdenes consulta el historiador oficial
(`/api/historian`, `/api/historial-ordenes`) y degrada a caché si el enlace
está caído.

Un servidor **MCP** real con transporte `stdio` (JSON-RPC 2.0) expone esas
tools:

```powershell
python -m app.mcp
```

Además existe un wrapper HTTP en `/api/mcp/tools` y `/api/mcp/call` para
pruebas; no se presenta como transporte MCP stdio/SSE.

El RAG indexa `datos/documentos/fragmentos.jsonl` con metadatos de equipo,
fabricante, documento, sección, cita y vigencia (excluye la Rev. C vencida).
La métrica `evaluate_official` reporta hit/recall/distractor@k sobre las 71
preguntas de `evaluacion/retrieval.json`.

## Memoria

`ConversationMemory` conserva el estado de la conversación de cada nota
(mensaje de tablet, nota, borrador, intento) con retención de 45 días. Cuando
`DATABASE_URL` apunta a PostgreSQL, se persiste en la tabla
`conversation_memory`; sin base, opera en RAM con la misma política.

## Datos y modelo Whisper

`datos/` contiene `planta.yaml`, `materiales.yaml`, el corpus documental y la
suite de retrieval. El modelo Whisper se obtiene de forma reproducible con
revisión fija:

```powershell
python -m pip install -e ".[voice]"
python scripts\download_whisper.py
```

El contenedor lo descarga al iniciar (en `/models/whisper-small`) si el
directorio `models/` está vacío, y lo reutiliza en los arranques siguientes.
