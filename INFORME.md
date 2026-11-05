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
| Transcripción | `Transcriber` configurable; fixture local incluido | Adaptador local, sin nube |
| Extracción estructurada | `VoicePartExtractor`/adaptador de modelo cerrado | CPU de planta |
| Recuperación | pgvector previsto + índice reproducible | PostgreSQL 16 |
| Herramientas | Pydantic + FastAPI + MCP | Red local de planta |

No se declara un modelo cerrado no entregado por la cátedra. Cuando se provea
la lista oficial, se completa el adaptador con nombre, proveedor, versión,
parámetros y benchmark sin modificar el dominio.

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

La suite actual cubre idempotencia, anomalía sostenida, seguridad offline,
aprobación, cola de sincronización, API y contratos estrictos. La evaluación
final debe ejecutar los escenarios del anexo y reportar aciertos por campo,
preguntas, recall@k, latencia, tokens y costo.

Sobre el corpus oficial local de 701 fragmentos, el índice reproducible obtiene
`hit@5=0,803`, `recall@5=0,695` y `distractor@5=0,000` en las 71 preguntas.
La métrica queda expuesta por `ManualIndex.evaluate_official`; el benchmark
puede seguir mejorándose con embeddings pgvector sin cambiar el contrato de
citas.

## Decisiones y límites conocidos

Los fixtures locales permiten ejecutar la entrega sin acceso al simulador,
corpus o modelos oficiales. La integración HTTP, el transporte MCP y el
backend pgvector se mantienen detrás de interfaces para evitar que una
dependencia externa altere la seguridad operacional.
