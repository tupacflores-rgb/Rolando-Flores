"""Tests de la Entrega 1: RAG con metadatos por equipo y fabricante (P2)."""

from app.models import RetrievalQuery
from app.rag import ManualIndex


def _index():
    return ManualIndex.from_jsonl("datos/documentos/fragmentos.jsonl")


def test_search_by_equipment_returns_fragments():
    index = _index()
    results = index.search(RetrievalQuery(question="presión de descarga", equipment_tag="B-101", k=10))
    assert results
    # La bomba TX-350 aplica a B-101.
    assert any("TX350-D" in r.chunk.document for r in results)


def test_filter_search_returns_fc48():
    index = _index()
    results = index.search(RetrievalQuery(question="cartuchos filtro diferencial", equipment_tag="F-201B", k=10))
    assert any(r.chunk.document == "FC48-3" for r in results)


def test_metadata_derived_from_document():
    index = _index()
    tags = {c.equipment_tag for c in index.chunks}
    assert "general" not in tags or any(c.equipment_tags for c in index.chunks)
    manufacturers = {c.manufacturer for c in index.chunks}
    assert "desconocido" not in manufacturers
    assert "Trimax Industrial" in manufacturers
    assert "Filtrapat" in manufacturers


def test_rev_c_excluded():
    index = _index()
    results = index.search(RetrievalQuery(question="límites de operación de la bomba", k=20))
    assert results
    assert all(r.chunk.document != "TX350-C" for r in results)
    # Ningún fragmento vencido se devuelve.
    assert all(r.chunk.vigente for r in results)


def test_official_metrics():
    index = _index()
    metrics = index.evaluate_official("datos/documentos/evaluacion/retrieval.json")
    assert metrics["n"] == 71
    total = metrics["total"]
    assert 0.0 <= total["hit@5"] <= 1.0
    assert 0.0 <= total["recall@5"] <= 1.0
    assert total["hit@5"] >= 0.5
    assert total["recall@5"] >= 0.5
