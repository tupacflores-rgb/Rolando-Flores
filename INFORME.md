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
| Extracción estructurada | `VoicePartExtractor`/adaptador de modelo cerrado | CPU de planta |
| Recuperación | pgvector previsto + índice reproducible | PostgreSQL 16 |
| Herramientas | Pydantic + FastAPI + MCP | Red local de planta |

El modelo se descarga con `scripts/download_whisper.py` desde
`Systran/faster-whisper-small` usando una revisión fija. Los pesos no se
versionan en Git por su tamaño; un clon limpio puede obtenerlos de forma
reproducible antes de montar `models/`.

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

El corpus oficial y su evaluación están incluidos en `datos/documentos/`.
La integración HTTP, el transporte MCP completo y el backend pgvector se
mantienen detrás de interfaces; la superficie MCP actual es un adaptador HTTP
local y no debe presentarse como transporte MCP stdio/SSE. La memoria de
conversación mantiene retención de 45 días en el proceso; todavía no se
persiste en PostgreSQL, por lo que un reinicio elimina esa memoria aunque no
el estado de órdenes, sensores y sincronización.
