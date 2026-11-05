from datetime import UTC, datetime, timedelta

from app.domain import DomainService, detect_safety
from app.integrations import merge_corrected_rows
from app.models import Equipment, Event, EventStatus, FilaParte, Order, SensorReading, VoiceNote
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


def test_reserve_is_excluded_when_maintaining_itself():
    service = _official_service()
    order = service.create_order(
        Order(
            event_id=_event("B-103").id,
            equipment_tag="B-103",
            task="T-B-EMP",
            parts=[],
            total_cost_usd=0,
            stock_available=False,
            standard_task=False,
            keeps_injection=False,
            internal_staff=False,
        )
    )
    assert order.status == "Pendiente de aprobación"


def test_automatic_order_uses_catalog_task_and_deduplicates():
    service = _official_service()
    event = _event("B-101").model_copy(
        update={"variable": "vibracion", "context": {"trend": [1, 2]}}
    )
    service._remember_event(event)
    first = service._ensure_order_for_event(event)
    second = service._ensure_order_for_event(event)
    assert first.id == second.id
    assert first.task == "Análisis de vibraciones con colector"
    assert first.evidence["event_id"] == str(event.id)
    assert first.status == "Pendiente de aprobación"


def test_automatic_order_reuses_open_order_for_same_equipment():
    service = _official_service()
    first_event = _event("B-101")
    second_event = _event("B-101").model_copy(
        update={"idempotency_key": "event-B-101-second"}
    )
    first = service._ensure_order_for_event(first_event)
    second = service._ensure_order_for_event(second_event)
    assert first.id == second.id


def test_offline_queue_replaces_unsynced_payload():
    service = DomainService()
    first = service.enqueue("order", "order-1", {"estado": "Pendiente"})
    second = service.enqueue("order", "order-1", {"estado": "Aprobada"})
    assert first is second
    assert second["payload"] == {"estado": "Aprobada"}


def test_ambiguous_equipment_exposes_options():
    from app.integrations import AmbiguousInputError, VoicePartExtractor

    extractor = VoicePartExtractor(
        [
            Equipment(tag="B-101", name="Bomba", kind="bomba"),
            Equipment(tag="B-102", name="Bomba", kind="bomba"),
        ]
    )
    try:
        extractor.extract(
            VoiceNote(note_id="ambiguous", observed_at=datetime.now(UTC)),
            "La bomba está en 100 bar",
        )
    except AmbiguousInputError as exc:
        assert exc.options == ["B-101", "B-102"]
    else:
        raise AssertionError("La ambigüedad no fue reportada")


def test_http_tablet_correction_preserves_rows():
    import app.main as main
    from fastapi.testclient import TestClient

    main.service.__init__()
    main.draft_rows.clear()
    main.draft_notes.clear()
    main.tablet_notes.clear()
    main.pending_questions.clear()
    client = TestClient(main.app)
    for equipment in (
        Equipment(
            tag="B-101",
            name="Bomba uno",
            aliases=["la uno"],
            kind="bomba",
        ),
        Equipment(
            tag="B-102",
            name="Bomba dos",
            aliases=["la dos"],
            kind="bomba",
        ),
    ):
        main.service.add_equipment(equipment)
    created = client.post(
        "/api/recorridas/procesar",
        json={
            "note_id": "HTTP-CORRECTION",
            "observed_at": datetime.now(UTC).isoformat(),
            "transcript": "la uno está en 100 kg/cm2 y la dos está en 120 psi",
        },
    )
    assert created.status_code == 200
    corrected = client.post(
        "/api/tablet/respuesta",
        json={
            "note_id": "HTTP-CORRECTION",
            "accepted": False,
            "corrections": "No, la uno estaba en 115 kg/cm2",
        },
    )
    assert corrected.status_code == 200
    assert [(row["equipment_tag"], row["value"]) for row in corrected.json()] == [
        ("B-101", 115),
        ("B-102", 120),
    ]


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
