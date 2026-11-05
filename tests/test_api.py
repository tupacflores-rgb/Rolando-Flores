from fastapi.testclient import TestClient

from app.main import app, service

client = TestClient(app)


def setup_function():
    service.__init__()


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
