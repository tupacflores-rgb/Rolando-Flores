# Informe técnico

## Alcance

La entrega separa las decisiones críticas del dominio de cualquier modelo:
límites, sostenimiento, seguridad, idempotencia, aprobación, estados y
certificación son deterministas. Los adaptadores de voz, RAG y MCP tienen
contratos estrictos y pueden reemplazarse por los servicios oficiales.

## Modelos y hardware

| Tarea | Implementación | Ejecución |
|---|---|---|
| Detección, seguridad y aprobación | Python determinista | CPU de planta, 4 cores, 8 GB |
| Transcripción | `faster-whisper-small` con revisión fija; fixture local incluido | CPU de planta, sin nube |
| Extracción estructurada | `VoicePartExtractor` determinista (regex + números en palabras) | CPU de planta |
| Recuperación | Índice léxico BM25 reproducible (pgvector es el backend previsto) | PostgreSQL 16 |
| Herramientas | Pydantic + FastAPI + servidor MCP (stdio, JSON-RPC) | Red local de planta |

El modelo se descarga con `scripts/download_whisper.py` desde
`Systran/faster-whisper-small` usando una revisión fija. Los pesos no se
versionan en Git por su tamaño; un clon limpio puede obtenerlos de forma
reproducible antes de montar `models/`, o el contenedor los descarga en el
primer arranque.

## Tokens, costo y latencia

Las etapas deterministas y el índice local consumen cero tokens y no tienen
costo de proveedor. Para un modelo oficial, el adaptador debe registrar
modelo, tokens de entrada/salida, duración, reintentos y costo por llamada en
`ToolAudit`. Las alertas S1-S4 no esperan respuesta y deben publicarse dentro
de 30 segundos reales.

## Fuentes de datos

- Límites, stock, historial de sensores y órdenes: API/SQL operativo.
- Manuales, causas y acciones: RAG con documento, equipo, sección, vigencia y
  cita.
- Precio de una habilita: contrato, nunca el texto declarado por la
  contratista.

## Validación

La suite actual cubre idempotencia, anomalía sostenida por variable, seguridad
offline, aprobación con cantidades de stock, correcciones parciales de voz,
cola de sincronización, API y contratos estrictos. La evaluación
final debe ejecutar los escenarios del anexo y reportar aciertos por campo,
preguntas, recall@k, latencia, tokens y costo.

Sobre el corpus oficial local de 701 fragmentos, el índice reproducible obtiene
`hit@5=0,803`, `recall@5=0,695` y `distractor@5=0,000` en las 71 preguntas.
La métrica queda expuesta por `ManualIndex.evaluate_official`; el benchmark
puede seguir mejorándose con embeddings pgvector sin cambiar el contrato de
citas.

## Decisiones y límites conocidos

El corpus oficial y su evaluación están incluidos en `datos/documentos/`. El
índice RAG es léxico (BM25) y determinista: no usa embeddings; pgvector queda
como backend previsto para una etapa posterior. El servidor MCP expone las
tools por transporte `stdio` (JSON-RPC 2.0); el wrapper HTTP `/api/mcp/*` es
solo para pruebas y no se presenta como transporte MCP. La memoria de
conversación se persiste en PostgreSQL (`conversation_memory`) cuando hay
`DATABASE_URL`; sin base, opera en RAM con la misma política de retención de
45 días.
