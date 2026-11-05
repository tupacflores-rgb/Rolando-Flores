from datetime import UTC, datetime, timedelta

from app.domain import DomainService, detect_safety
from app.integrations import merge_corrected_rows
from app.models import Equipment, Event, EventStatus, FilaParte, Order, SensorReading
from app.official_data import catalog_from_materials, load_material_catalog, load_equipment


def _official_service() -> DomainService:
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


def _event(tag: str = "F-201B") -> Event:
    return Event(
        idempotency_key=f"event-{tag}",
        origin="sensor",
        source_id=f"sensor-{tag}",
        status=EventStatus.ESCALATED,
        equipment_tag=tag,
    )


def test_f201b_cartuchos_uses_required_quantity():
    service = _official_service()
    order = service.create_order(
        Order(
            event_id=_event().id,
            equipment_tag="F-201B",
            task="T-F-CAR",
            parts=["TX-VAL-KIT"],
            total_cost_usd=1,
            stock_available=True,
            standard_task=True,
            keeps_injection=True,
            internal_staff=True,
        )
    )
    assert order.status == "Pendiente de aprobación"
    assert order.parts == ["FC-CART-10"]
    assert order.total_cost_usd == 17 * 48


def test_b101_empaquetadura_can_use_available_reserve():
    service = _official_service()
    order = service.create_order(
        Order(
            event_id=_event("B-101").id,
            equipment_tag="B-101",
            task="T-B-EMP",
            parts=[],
            total_cost_usd=0,
            stock_available=False,
            standard_task=False,
            keeps_injection=False,
            internal_staff=False,
        )
    )
    assert order.status == "Aprobada"
    assert order.keeps_injection is True


def test_nonstandard_task_does_not_keep_client_parts():
    service = _official_service()
    order = service.create_order(
        Order(
            event_id=_event("B-101").id,
            equipment_tag="B-101",
            task="cambio especial no catalogado",
            parts=["TX-VAL-KIT"],
            total_cost_usd=1,
            stock_available=True,
            standard_task=False,
            keeps_injection=True,
            internal_staff=True,
        )
    )
    assert order.parts == []
    assert order.status == "Pendiente de aprobación"


def test_safety_connectors_are_not_negations():
    assert [a.code for a in detect_safety("Sin duda hay fuego", "1")] == ["S3"]
    assert [a.code for a in detect_safety("Sin embargo hay humo", "2")] == ["S3"]
    assert detect_safety("No hay humo", "3") == []
    assert [a.code for a in detect_safety("No hay olor a gas, pero hay fuego", "4")] == ["S3"]
    assert [a.code for a in detect_safety("No hay persona lesionada, pero hay humo", "5")] == ["S3"]


def test_temperature_limit_sustains_using_variable_limit():
    service = _official_service()
    times = [datetime.now(UTC), datetime.now(UTC) + timedelta(minutes=1)]
    first = service.evaluate_sensor(
        SensorReading(
            idempotency_key="temperature-1",
            equipment_tag="B-101",
            variable="temperatura_aceite",
            value=100,
            unit="C",
            observed_at=times[0],
        )
    )
    second = service.evaluate_sensor(
        SensorReading(
            idempotency_key="temperature-2",
            equipment_tag="B-101",
            variable="temperatura_aceite",
            value=101,
            unit="C",
            observed_at=times[1],
        )
    )
    assert first.status == EventStatus.NORMAL
    assert second.status == EventStatus.ESCALATED


def test_partial_voice_correction_preserves_other_rows():
    observed_at = datetime.now(UTC)
    rows = [
        FilaParte(
            equipment_tag="B-101",
            variable="presion_descarga",
            value=100,
            unit="kg/cm2",
            observed_at=observed_at,
        ),
        FilaParte(
            equipment_tag="B-102",
            variable="presion_descarga",
            value=120,
            unit="psi",
            observed_at=observed_at,
        ),
    ]
    corrected = rows[0].model_copy(update={"value": 115})
    result = merge_corrected_rows(rows, [corrected])
    assert [(row.equipment_tag, row.value) for row in result] == [
        ("B-101", 115),
        ("B-102", 120),
    ]
