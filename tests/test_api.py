import json

from fastapi.testclient import TestClient

from app.main import app, draft_rows, memory, service
from app.models import Order

client = TestClient(app)


def setup_function():
    service.__init__()
    draft_rows.clear()
    memory.__init__()


def test_health_and_strict_contract():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["enlace_ok"] is False
    invalid = client.post(
        "/api/equipos",
        json={"tag": "B-101", "name": "Bomba", "kind": "bomba", "unexpected": True},
    )
    assert invalid.status_code == 422


def test_equipment_part_and_sensor_flow():
    assert client.post(
        "/api/equipos",
        json={"tag": "B-101", "name": "Bomba 1", "kind": "bomba", "alarm_max": 110},
    ).status_code == 201
    part = client.post(
        "/api/partes",
        json={
            "idempotency_key": "part-1",
            "operator_id": "operator",
            "observed_at": "2026-11-04T10:00:00Z",
            "readings": [
                {"equipment_tag": "B-101", "variable": "presion", "value": 100, "unit": "kg/cm2"}
            ],
        },
    )
    assert part.status_code == 201
    events = client.post("/api/partes/part-1/confirmar")
    assert events.status_code == 200
    assert events.json()[0]["status"] == "Sin novedad"


def test_voice_tablet_and_memory_flow():
    assert client.post(
        "/api/equipos",
        json={"tag": "B-103", "name": "Bomba reserva", "kind": "bomba", "aliases": ["la tres"]},
    ).status_code == 201
    response = client.post(
        "/api/recorridas/procesar",
        json={
            "note_id": "VIVO-API-1",
            "observed_at": "2026-11-05T10:00:00Z",
            "transcript": "La tres está en ciento diez bar",
        },
    )
    assert response.status_code == 200
    assert response.json()[0]["equipment_tag"] == "B-103"
    corrected = client.post(
        "/api/tablet/respuesta",
        json={"note_id": "VIVO-API-1", "accepted": True},
    )
    assert corrected.status_code == 200
    assert client.get("/api/memoria/VIVO-API-1").json()


def _escalated_event() -> dict:
    assert client.post(
        "/api/equipos",
        json={"tag": "B-101", "name": "Bomba 1", "kind": "bomba", "alarm_max": 110},
    ).status_code == 201
    readings = [
        ("sensor-1", 100, "2026-11-05T10:00:00Z"),
        ("sensor-2", 120, "2026-11-05T10:01:00Z"),
        ("sensor-3", 121, "2026-11-05T10:02:00Z"),
    ]
    for key, value, observed_at in readings:
        response = client.post(
            "/api/sensores",
            json={
                "idempotency_key": key,
                "equipment_tag": "B-101",
                "variable": "presion_descarga",
                "value": value,
                "unit": "kg/cm2",
                "observed_at": observed_at,
            },
        )
        assert response.status_code == 200
    events = client.get("/api/eventos").json()
    return next(event for event in events if event["status"] == "Escalado")


def _order_payload(event_id: str, *, internal_staff: bool) -> dict:
    return {
        "event_id": event_id,
        "equipment_tag": "B-101",
        "task": "inspeccion",
        "parts": ["EMP-1"],
        "total_cost_usd": 100,
        "stock_available": True,
        "standard_task": True,
        "keeps_injection": True,
        "internal_staff": internal_staff,
        "structural_damage": False,
    }


def _executed_contractor_order() -> str:
    event = _escalated_event()
    created = client.post(
        "/api/ordenes",
        json=_order_payload(event["id"], internal_staff=False),
    )
    assert created.status_code == 200
    order_id = created.json()["id"]
    for target in ("Aprobada", "Ejecutada"):
        transition = client.post(
            f"/api/ordenes/{order_id}/transicion",
            params={"target": target},
        )
        assert transition.status_code == 200
    closure = {
        "order_id": order_id,
        "technician": "contratista",
        "contractor": True,
        "tasks_done": ["inspeccion"],
        "parts_used": ["EMP-1"],
        "hours": 1,
        "final_test": "110 kilos sin pérdida",
    }
    assert client.post(f"/api/ordenes/{order_id}/cierre", json=closure).status_code == 200
    return order_id


def test_create_order_from_escalated_event():
    event = _escalated_event()
    response = client.post(
        "/api/ordenes",
        json=_order_payload(event["id"], internal_staff=True),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == event["id"]
    assert body["status"] == "Aprobada"


def test_certification_without_prices_keeps_order_executed(monkeypatch):
    monkeypatch.delenv("CONTRACT_PRICES_JSON", raising=False)
    order_id = _executed_contractor_order()
    response = client.post(f"/api/ordenes/{order_id}/certificar")
    assert response.status_code == 503
    assert service.orders[order_id].status == "Ejecutada"
    assert service.orders[order_id].habilita is None


def test_certification_persists_habilita_on_order(monkeypatch):
    monkeypatch.setenv("CONTRACT_PRICES_JSON", json.dumps({"EMP-1": 125}))
    order_id = _executed_contractor_order()
    response = client.post(f"/api/ordenes/{order_id}/certificar")
    assert response.status_code == 200
    body = response.json()
    assert body["habilita"]["amount_usd"] == 125
    assert body["order"]["status"] == "Certificada"
    restored = Order.model_validate(service.orders[order_id].model_dump(mode="json"))
    assert restored.closure is not None
    assert restored.habilita is not None
    assert restored.habilita.amount_usd == 125
