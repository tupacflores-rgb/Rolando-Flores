# Etapa 5 — RAG, evaluación y memoria

**Herramientas:** PostgreSQL 16, pgvector, índice local reproducible, JSON,
pytest y métricas recall@k.

**Conceptos:** chunking, metadatos, vigencia, grounding, cita verificable,
BM25 como baseline, context builder, retención y minimización de memoria.

`app/rag.py` carga el corpus oficial desde `fragmentos.jsonl`, filtra
documentos vencidos y por equipo antes de rankear, y puede evaluar contra
`retrieval.json`. Cada resultado conserva documento, sección y cita. Límites,
stock e historial operativo siguen consultándose por API/SQL, no por RAG.
`app/memory.py` retiene
solo el estado operativo de la nota durante 45 días y ofrece purga.

**Verificación:** ejecutar la suite de retrieval cuando esté disponible y
comparar `hit_at_k`/`recall_at_k` contra la línea base indicada por el anexo.
