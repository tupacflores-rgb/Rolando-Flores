# Etapa 4 — Anomalías y órdenes

**Herramientas:** Python, Pydantic, PostgreSQL, API de historial, API de stock y
tests de dominio.

**Conceptos:** evidencia, tendencia, causa probable, regla de aprobación,
separación de responsabilidades y suspensión persistida.

Las órdenes se aprueban automáticamente solo con tarea estándar, inyección
mantenida, stock, costo menor a USD 2.500 y personal propio. El daño
estructural siempre exige revisión humana. Los motivos quedan en
`approval_reasons` y las transiciones inválidas se rechazan.

**Verificación:** ejecutar la parametrización de `tests/test_domain.py` para
los casos aprobables y pendientes.
