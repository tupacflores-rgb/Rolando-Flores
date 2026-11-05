# Etapa 1 — Dominio determinista y offline

**Herramientas:** Python, Pydantic, FastAPI, PostgreSQL/SQL, pytest, HTTPX,
PowerShell y curl.

**Conceptos:** funciones puras, máquina de estados, idempotencia, claves únicas,
anomalía sostenida, alerta local S1-S4, transacción, reintento y cola offline.

`app/domain.py` decide límites y transiciones sin LLM. Un pico aislado no escala,
`parada, en reserva` es normal y las alertas de seguridad no dependen de la
nube. `app/models.py` rechaza campos desconocidos con `extra="forbid"`.

**Verificación:** `python -m pytest tests/test_domain.py tests/test_api.py`.
