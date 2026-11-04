# Planta de inyección de agua

Núcleo operativo determinista de la etapa sin LLM. La planta puede registrar
partes estructurados, evaluar lecturas, detectar condiciones inseguras y mantener
una cola offline sin depender de internet ni de un modelo.

## Ejecución

Requiere Python 3.11+ y Docker Compose:

```powershell
docker compose up --build
```

La API queda en `http://localhost:8000`; la documentación OpenAPI está en
`/docs` y el healthcheck en `/health`.

Para ejecutar las pruebas localmente:

```powershell
python -m pip install -e ".[test]"
pytest
```

## Arquitectura planta/nube

La API y el detector S1-S4 corren en la PC de planta. PostgreSQL 16 con pgvector
se levanta en el mismo Compose: pgvector queda disponible para una etapa RAG
posterior, pero no participa en las decisiones de esta etapa. La sincronización
externa se modela como cola idempotente ordenada; si el enlace cae, las
operaciones quedan pendientes y no se pierde el estado local.

No se usa transcripción, extracción, RAG ni LLM en esta etapa. Las reglas de
límites, sostenimiento, seguridad y aprobación están en código y son
reproducibles.

## Endpoints principales

- `POST /api/equipos`, `GET /api/equipos`
- `POST /api/partes`, `POST /api/partes/{clave}/confirmar`
- `POST /api/sensores`, `GET /api/eventos`
- `GET /api/alertas-seguridad`
- `POST /api/ordenes`, `POST /api/ordenes/{id}/transicion`
- `GET /api/tools/equipos`, `GET /api/tools/sensores`
- `GET /api/sincronizacion/pendientes`

Las tools exponen solo lectura y validan contratos estrictos con Pydantic
(`extra="forbid"`). Las órdenes se aprueban automáticamente únicamente si la
tarea es estándar, conserva la inyección, hay stock, el costo es menor a USD
2.500 y trabaja personal propio. Cualquier excepción queda pendiente de
aprobación.
