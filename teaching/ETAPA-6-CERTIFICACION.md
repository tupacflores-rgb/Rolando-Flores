# Etapa 6 — Cierre y certificación

**Herramientas:** Pydantic, Python, PostgreSQL y tests de comparación.

**Conceptos:** cierre con evidencia, diferencia esperada/real, supervisor,
inspector, contrato, precio autoritativo y habilita.

`app/certification.py` compara tareas y repuestos de la orden con el cierre.
Una habilita se calcula desde la orden y los precios del contrato, nunca desde
un monto declarado por la contratista.

**Verificación:** probar cierre coincidente, faltantes, extras y cálculo de
`HAB-<id>` con precios contractuales.
