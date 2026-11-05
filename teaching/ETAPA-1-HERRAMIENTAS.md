# Teaching — herramientas de la etapa 1

## Objetivo

Esta guía enumera las herramientas que se usarán para construir la primera etapa
del proyecto: el núcleo determinista sin LLM.

La idea es aprender qué hace cada herramienta, por qué se eligió, cómo participa
en el sistema y qué parte del código generado debe poder explicarse sin depender
de la IA.

En esta etapa no se usan modelos de lenguaje para transcribir, extraer datos,
analizar manuales ni decidir aprobaciones.

## Herramientas principales

| Herramienta | Uso en el proyecto | Qué aprender |
|---|---|---|
| **Git** | Control de versiones del código y seguimiento de cambios. | Commits, ramas, historial, `diff`, `status` y recuperación de cambios. |
| **GitHub** | Repositorio remoto y entrega del proyecto. | Repositorios, README, revisiones y publicación del código. |
| **Docker** | Empaquetar y ejecutar los servicios en contenedores. | Imágenes, contenedores, volúmenes, redes y variables de entorno. |
| **Docker Compose** | Levantar la API, PostgreSQL y servicios auxiliares juntos. | Servicios, dependencias, healthchecks, redes y límites de recursos. |
| **Python 3.11+** | Lenguaje principal del backend y de la lógica determinista. | Tipos, módulos, excepciones, `async`, paquetes y estructura de aplicaciones. |
| **FastAPI** | API HTTP para recibir datos y exponer consultas. | Rutas, dependencias, validación, códigos HTTP y documentación OpenAPI. |
| **Pydantic** | Validar requests, responses y contratos de las tools. | Modelos, tipos estrictos, validación y rechazo de campos inesperados. |
| **PostgreSQL 16** | Persistir equipos, partes, sensores, eventos, alertas, órdenes y cola. | Tablas, claves, índices, transacciones, constraints y consultas SQL. |
| **pgvector** | Dejar disponible la extensión para la futura etapa RAG. | Extensiones PostgreSQL y por qué no se usa todavía para decisiones de etapa 1. |
| **SQLAlchemy** | Acceso tipado y organizado a PostgreSQL desde Python. | Engine, sesiones, modelos, consultas y transacciones. |
| **Alembic** | Crear y versionar migraciones de la base de datos. | Migraciones incrementales y evolución segura del esquema. |
| **pytest** | Tests unitarios y de integración. | Fixtures, parametrización, mocks y asserts reproducibles. |
| **HTTPX** | Probar la API FastAPI y simular clientes HTTP. | Requests de prueba, respuestas, timeouts y cliente async. |
| **Ruff** | Linting y formateo rápido del código Python. | Errores de estilo, imports y formato consistente. |
| **mypy** | Verificación estática de tipos Python. | Anotaciones, contratos y detección de errores antes de ejecutar. |

## Herramientas de operación y diagnóstico

| Herramienta | Uso en el proyecto | Qué aprender |
|---|---|---|
| **PowerShell** | Ejecutar comandos en Windows y automatizar tareas locales. | Navegación, variables, scripts y ejecución de tests. |
| **Terminal** | Ejecutar Git, Docker, Python y los comandos del proyecto. | Flujo de trabajo reproducible desde línea de comandos. |
| **curl** | Probar endpoints HTTP desde la terminal. | Métodos HTTP, headers, JSON, códigos de respuesta y errores. |
| **pgAdmin** o **psql** | Inspeccionar PostgreSQL y consultar datos. | Consultas, transacciones y diagnóstico de persistencia. |
| **Docker logs** | Revisar el comportamiento de los servicios. | Logs, errores de arranque, healthchecks y diagnóstico entre contenedores. |
| **OpenAPI / Swagger UI** | Explorar y probar la API documentada por FastAPI. | Contratos HTTP y validación interactiva de endpoints. |

## Herramientas de diseño y documentación

| Herramienta | Uso en el proyecto | Qué aprender |
|---|---|---|
| **Markdown** | README, especificaciones y documentación técnica. | Documentar decisiones y procedimientos de forma clara. |
| **Mermaid** | Diagramas opcionales de arquitectura y estados. | Representar flujos, dependencias y máquinas de estados. |
| **Diagrama de estados** | Documentar estados de Parte, Evento y Orden. | Transiciones válidas e invariantes del dominio. |
| **Diagrama de secuencia** | Documentar el flujo API → dominio → base de datos → cola. | Orden de operaciones y manejo de errores. |

## Conceptos que deben aprenderse junto con las herramientas

- **API REST:** recursos, métodos HTTP, códigos de estado y errores.
- **Validación de datos:** diferencia entre datos faltantes, inválidos y ambiguos.
- **Persistencia transaccional:** commit, rollback, aislamiento e idempotencia.
- **Claves únicas:** impedir eventos, órdenes y sincronizaciones duplicadas.
- **Máquinas de estados:** transiciones permitidas para partes, eventos y órdenes.
- **Reglas deterministas:** mismos datos de entrada producen siempre el mismo resultado.
- **Anomalía sostenida:** no escalar un pico aislado sin evidencia suficiente.
- **Cola offline:** guardar pendientes, reintentar en orden y sincronizar sin duplicar.
- **Healthcheck:** distinguir un contenedor iniciado de un servicio realmente disponible.
- **Tests unitarios:** verificar reglas aisladas sin depender de servicios externos.
- **Tests de integración:** verificar API, base de datos y cola trabajando juntas.
- **Observabilidad:** registrar decisiones, errores, tiempos, reintentos y contexto.
- **Seguridad operacional:** las alertas S1-S4 deben funcionar localmente y sin nube.

## Qué no se usa todavía

- LLM local o en la nube.
- LangChain para agentes.
- Transcripción de audio.
- Visión artificial.
- RAG, embeddings y búsqueda semántica.
- MCP para tools agénticas.

Estas tecnologías pertenecen a etapas posteriores. En la etapa 1 se preparan
contratos y límites para incorporarlas sin modificar las reglas críticas del
dominio.

## Método de aprendizaje para cada herramienta

Para cada herramienta se debe poder responder:

1. ¿Qué problema resuelve?
2. ¿Dónde aparece en el repositorio?
3. ¿Qué configuración necesita?
4. ¿Qué errores puede producir?
5. ¿Cómo se prueba?
6. ¿Qué parte del sistema dejaría de funcionar si se elimina?
7. ¿Qué decisión tomó la IA y cómo se puede verificar manualmente?

## Comandos de referencia

```powershell
# Ver el estado del repositorio
git status

# Construir y levantar los servicios
docker compose up --build

# Ejecutar los tests
pytest

# Revisar estilo y formato
ruff check .
ruff format --check .

# Revisar tipos
mypy .

# Consultar la API local
curl http://localhost:8000/health
```

Los comandos exactos pueden ajustarse cuando se cree la estructura definitiva
del proyecto, pero toda modificación debe documentarse en el README.
