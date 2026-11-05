# Etapa 0 — Requisitos y arquitectura

**Herramientas:** Git, GitHub, Markdown, Docker Compose, Python, FastAPI,
PostgreSQL y Mermaid.

**Conceptos:** requisitos funcionales, separación planta/nube, contratos,
restricciones de recursos, healthcheck, red externa y trazabilidad.

La planta conserva detección, seguridad, estado y cola offline. La nube queda
para tareas que no son necesarias durante la caída del enlace. `docker-compose.yml`
declara la red `planta-lan`, la etiqueta `academia.planta=pc`, límites y
PostgreSQL 16 con pgvector. El diseño se documenta en `context/plan`.

**Verificación:** `docker network create planta-lan` y luego
`docker compose up --build`; consultar `/health` y `/docs`.
