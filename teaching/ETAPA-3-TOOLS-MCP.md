# Etapa 3 — Tools y MCP

**Herramientas:** Pydantic, FastAPI, HTTPX, MCP, pytest y logs estructurados.

**Conceptos:** tool read-only, contrato estricto, timeout, retry, auditoría,
presupuesto de respuesta y separación entre consulta y escritura.

`app/tools.py` contiene consultas de equipos e historial. `app/mcp.py` expone
la consulta de equipos mediante una superficie MCP mínima; el transporte puede
conectarse en el despliegue. Ninguna tool aprueba órdenes ni muta inventario.

**Verificación:** enviar un campo extra y esperar 422; llamar un nombre MCP
desconocido y obtener un error explícito.
