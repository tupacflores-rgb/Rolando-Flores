"""Tests de la Entrega 1: cierre por voz (P1)."""

from datetime import UTC, datetime
from uuid import uuid4

from app.certification import compare_closure
from app.integrations import ClosureExtractor
from app.models import ClosureReport, Event, EventStatus, Order, OrderStatus
from app.official_data import catalog_from_materials, load_equipment, load_material_catalog


def _catalogs():
    inventory, materials, tasks = catalog_from_materials(
        load_material_catalog("datos/materiales.yaml")
    )
    return inventory, tasks


def _closure_extractor():
    inventory, tasks = _catalogs()
    return ClosureExtractor(tasks, inventory)


def test_closure_extractor_correct():
    extractor = _closure_extractor()
    parsed = extractor.extract(
        "Cierro la orden CIERRE 1. Hice cambio de empaquetadura. "
        "Usé un kit de empaquetadura TX-350. Probé a ciento diez kilos, sin pérdida. "
        "Fueron dos horas."
    )
    assert parsed is not None
    assert parsed["tasks_done"] == ["T-B-EMP"]
    assert parsed["parts_used"] == ["TX-EMP-KIT"]
    assert parsed["hours"] == 2.0
    assert "sin pérdida" in parsed["final_test"] or "sin perdida" in parsed["final_test"]


def test_closure_extractor_unintelligible():
    assert _closure_extractor().extract("zzzz no se entiende nada") is None
    assert _closure_extractor().extract("Cierro la orden. Fueron dos horas.") is None


def test_closure_comparison_detects_extra_part():
    inventory, tasks = _catalogs()
    extractor = ClosureExtractor(tasks, inventory)
    parsed = extractor.extract(
        "Cierro la orden CIERRE 1. Hice cambio de empaquetadura. "
        "Usé un kit de empaquetadura TX-350, un juego de sellos de cárter TX-350. "
        "Probé a ciento diez kilos, sin pérdida. Fueron dos horas."
    )
    order = Order(
        event_id=uuid4(),
        equipment_tag="B-101",
        task="T-B-EMP",
        parts=["TX-EMP-KIT"],
        total_cost_usd=420,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=True,
    )
    closure = ClosureReport(
        order_id=order.id,
        technician="contratista",
        contractor=True,
        tasks_done=parsed["tasks_done"],
        parts_used=parsed["parts_used"],
        hours=parsed["hours"],
        final_test=parsed["final_test"],
    )
    comparison = compare_closure(order, closure)
    assert comparison.matches is False
    assert any("TX-SELLO-CAR" in diff for diff in comparison.differences)


def test_process_cierre_correct_goes_executed(monkeypatch):
    import app.main as main

    service = main.service
    service.__init__()
    inventory, materials, tasks = catalog_from_materials(
        load_material_catalog("datos/materiales.yaml")
    )
    service.inventory_catalog = inventory
    service.material_catalog = materials
    service.task_catalog = tasks
    order = Order(
        event_id=uuid4(),
        equipment_tag="B-101",
        task="T-B-EMP",
        parts=["TX-EMP-KIT"],
        total_cost_usd=420,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=True,
        status=OrderStatus.APPROVED,
    )
    service.orders[str(order.id)] = order

    note = type("NotaCierre", (), {
        "id": "CIERRE-1",
        "orden_id": str(order.id),
        "tecnico": "Ramón Cayupán",
        "empresa": "propio",
        "fotos": [],
    })()
    monkeypatch.setattr(main, "mqtt_bridge", None)
    main._process_cierre(
        note,
        "Cierro la orden. Hice cambio de empaquetadura. Usé un kit de empaquetadura TX-350. "
        "Probé a ciento diez kilos, sin pérdida. Fueron dos horas.",
    )
    assert order.status == OrderStatus.EXECUTED
    assert order.closure is not None
    assert order.closure.tasks_done == ["T-B-EMP"]


def test_process_cierre_difference_goes_observed(monkeypatch):
    import app.main as main

    service = main.service
    service.__init__()
    inventory, materials, tasks = catalog_from_materials(
        load_material_catalog("datos/materiales.yaml")
    )
    service.inventory_catalog = inventory
    service.material_catalog = materials
    service.task_catalog = tasks
    order = Order(
        event_id=uuid4(),
        equipment_tag="B-101",
        task="T-B-EMP",
        parts=["TX-EMP-KIT"],
        total_cost_usd=420,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=True,
        status=OrderStatus.APPROVED,
    )
    service.orders[str(order.id)] = order

    note = type("NotaCierre", (), {
        "id": "CIERRE-2",
        "orden_id": str(order.id),
        "tecnico": "Diego Barría (Servipat)",
        "empresa": "Servipat",
        "fotos": [],
    })()
    monkeypatch.setattr(main, "mqtt_bridge", None)
    main._process_cierre(
        note,
        "Cierro la orden. Hice cambio de empaquetadura. "
        "Usé un kit de empaquetadura TX-350, un juego de sellos de cárter TX-350. "
        "Probé a ciento diez kilos, sin pérdida. Fueron dos horas.",
    )
    assert order.status == OrderStatus.OBSERVED
    assert any("TX-SELLO-CAR" in reason for reason in order.approval_reasons)


def test_process_cierre_unintelligible_stays_approved(monkeypatch):
    import app.main as main

    service = main.service
    service.__init__()
    order = Order(
        event_id=uuid4(),
        equipment_tag="B-101",
        task="T-B-EMP",
        parts=["TX-EMP-KIT"],
        total_cost_usd=420,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=True,
        status=OrderStatus.APPROVED,
    )
    service.orders[str(order.id)] = order

    note = type("NotaCierre", (), {
        "id": "CIERRE-3",
        "orden_id": str(order.id),
        "tecnico": "Ramón Cayupán",
        "empresa": "propio",
        "fotos": [],
    })()
    monkeypatch.setattr(main, "mqtt_bridge", None)
    main._process_cierre(note, "zzzz ruido ininteligible")
    assert order.status == OrderStatus.APPROVED
    assert order.closure is None
