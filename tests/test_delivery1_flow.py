"""Tests de la Entrega 1: flujo completo y alertas de seguridad (criterios A/B)."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain import detect_safety
from app.main import app, service


def _reset():
    service.__init__()
    import app.main as main

    main.draft_rows.clear()
    main.draft_notes.clear()
    main.tablet_notes.clear()
    main.pending_questions.clear()
    main.mqtt_bridge = None


def test_detect_safety_s1_to_s4():
    assert [a.code for a in detect_safety("sale agua a presión para todos lados", "1")] == ["S1"]
    assert [a.code for a in detect_safety("hay olor a gas fuerte", "2")] == ["S2"]
    assert [a.code for a in detect_safety("sale humo del motor", "3")] == ["S3"]
    assert [a.code for a in detect_safety("mi compañero se golpeó la mano, está sangrando", "4")] == ["S4"]


def test_detect_safety_no_false_alarm_martes_tranquilo():
    # Frases de un martes tranquilo no deben disparar alertas.
    assert detect_safety("la dos está en mil seiscientos de descarga", "x") == []
    assert detect_safety("el rodamiento me dio cincuenta y dos grados", "x") == []
    assert detect_safety("el pulmón está en cinco metros", "x") == []
    assert detect_safety("la tres está parada, en reserva", "x") == []


def test_full_voice_flow_nota_tablet_confirm():
    _reset()
    client = TestClient(app)
    for equipment in (
        {"tag": "B-101", "name": "Bomba 1", "kind": "bomba", "aliases": ["la uno"], "alarm_max": 125, "alarm_min": 95},
        {"tag": "F-201B", "name": "Filtro B", "kind": "filtro", "aliases": ["el filtro B"]},
    ):
        client.post("/api/equipos", json=equipment)

    created = client.post(
        "/api/recorridas/procesar",
        json={
            "note_id": "FLOW-1",
            "observed_at": datetime.now(UTC).isoformat(),
            "transcript": "La uno está en ciento doce de descarga. El filtro B me dio uno ocho de diferencial.",
        },
    )
    assert created.status_code == 200
    rows = created.json()
    assert {(r["equipment_tag"], r["variable"]) for r in rows} == {
        ("B-101", "presion_descarga_local"),
        ("F-201B", "presion_diferencial"),
    }

    confirmed = client.post("/api/tablet/respuesta", json={"note_id": "FLOW-1", "accepted": True})
    assert confirmed.status_code == 200

    events = client.get("/api/eventos").json()
    # El diferencial 1.8 (> 1.5) escala F-201B; la descarga 112 está en rango.
    f_events = [e for e in events if e["equipment_tag"] == "F-201B"]
    assert f_events and f_events[0]["status"] == "Escalado"
    b_events = [e for e in events if e["equipment_tag"] == "B-101"]
    assert b_events and b_events[0]["status"] == "Sin novedad"


def test_ataque_no_aprueba_ni_carga_valvulas():
    from app.domain import DomainService
    from app.models import Event, EventStatus, Order
    from app.official_data import catalog_from_materials, load_equipment, load_material_catalog
    from uuid import uuid4

    s = DomainService()
    for equipment in load_equipment("datos/planta.yaml"):
        s.add_equipment(equipment)
    inventory, materials, tasks = catalog_from_materials(load_material_catalog("datos/materiales.yaml"))
    s.inventory_catalog = inventory
    s.material_catalog = materials
    s.task_catalog = tasks

    # La nota de ataque genera un escalado por goteo; la orden NO debe aprobarse sola
    # ni cargar el kit de válvulas (TX-VAL-KIT), por más que la nota lo pida.
    event = Event(
        idempotency_key="ataque-evento",
        origin="part",
        source_id=str(uuid4()),
        status=EventStatus.ESCALATED,
        equipment_tag="B-102",
        variable="goteo_empaquetadura",
    )
    s._remember_event(event)
    order = s._ensure_order_for_event(event)
    assert order.status == "Pendiente de aprobación"
    assert "TX-VAL-KIT" not in order.parts


def test_reserve_out_of_service_keeps_injection_only_with_replacement():
    from app.domain import DomainService
    from app.models import Order
    from app.official_data import catalog_from_materials, load_equipment, load_material_catalog
    from uuid import uuid4

    s = DomainService()
    for equipment in load_equipment("datos/planta.yaml"):
        s.add_equipment(equipment)
    inventory, materials, tasks = catalog_from_materials(load_material_catalog("datos/materiales.yaml"))
    s.inventory_catalog = inventory
    s.material_catalog = materials
    s.task_catalog = tasks
    s.pump_states["B-103"] = "disparada, no arranca"
    order = s.create_order(
        Order(
            event_id=uuid4(),
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
    assert order.keeps_injection is False
    assert order.status == "Pendiente de aprobación"
