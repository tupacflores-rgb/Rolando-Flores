"""Tests de la Entrega 1: reserva dinámica (P5)."""

from uuid import uuid4

from app.domain import DomainService
from app.models import Event, EventStatus, Order
from app.official_data import catalog_from_materials, load_equipment, load_material_catalog


def _service():
    service = DomainService()
    for equipment in load_equipment("datos/planta.yaml"):
        service.add_equipment(equipment)
    inventory, materials, tasks = catalog_from_materials(
        load_material_catalog("datos/materiales.yaml")
    )
    service.inventory_catalog = inventory
    service.material_catalog = materials
    service.task_catalog = tasks
    return service


def _order(equipment_tag: str) -> Order:
    return Order(
        event_id=uuid4(),
        equipment_tag=equipment_tag,
        task="T-B-EMP",
        parts=[],
        total_cost_usd=0,
        stock_available=False,
        standard_task=False,
        keeps_injection=False,
        internal_staff=False,
    )


def test_reserve_available_by_default():
    service = _service()
    order = service.create_order(_order("B-101"))
    assert order.keeps_injection is True
    assert order.status == "Aprobada"


def test_reserve_out_of_service_disparada():
    service = _service()
    service.pump_states["B-103"] = "disparada, no arranca"
    order = service.create_order(_order("B-101"))
    assert order.keeps_injection is False
    assert order.status == "Pendiente de aprobación"
    assert any("inyección" in reason for reason in order.approval_reasons)


def test_reserve_out_of_service_mantenimiento():
    service = _service()
    service.pump_states["B-103"] = "parada por mantenimiento"
    order = service.create_order(_order("B-102"))
    assert order.keeps_injection is False
    assert order.status == "Pendiente de aprobación"


def test_reserve_parada_en_reserva_sigue_disponible():
    service = _service()
    service.pump_states["B-103"] = "parada, en reserva"
    order = service.create_order(_order("B-101"))
    assert order.keeps_injection is True


def test_estado_report_marks_reserve_unavailable():
    service = _service()
    from app.models import Part, PartReading
    from datetime import UTC, datetime

    part = Part(
        idempotency_key="p-estado",
        operator_id="op",
        observed_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC),
        readings=[
            PartReading(
                equipment_tag="B-103",
                variable="estado",
                value=None,
                unit=None,
                observation="disparada, no arranca",
            )
        ],
    )
    service.save_part(part)
    service.confirm_part("p-estado")
    service.evaluate_part(part)
    assert service.pump_states["B-103"] == "disparada, no arranca"
    order = service.create_order(_order("B-101"))
    assert order.keeps_injection is False
