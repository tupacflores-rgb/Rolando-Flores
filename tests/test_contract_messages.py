import json
from datetime import UTC, datetime
from uuid import uuid4

import planta_contrato
from fastapi.testclient import TestClient

from app import main
from app.contract_messages import (
    alert_message,
    event_message,
    order_message,
    sensor_reading_from_contract,
    state_message,
    tablet_message,
)
from app.main import app, service
from app.official_data import equipment_from_definition
from app.models import (
    Equipment,
    Event,
    EventStatus,
    FilaParte,
    Order,
    OrderStatus,
    SafetyAlert,
)

client = TestClient(app)


class FakeMqtt:
    def __init__(self):
        self.published = []
        self.subscriptions = []

    def connect(self, *_args, **_kwargs):
        return 0

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def loop_start(self):
        return None

    def loop_stop(self):
        return None

    def disconnect(self):
        return None

    def publish(self, *args, **kwargs):
        self.published.append((args, kwargs))


def _event(status=EventStatus.ESCALATED, origin="part") -> Event:
    return Event(
        idempotency_key="event-1",
        origin=origin,
        source_id=str(uuid4()),
        status=status,
        equipment_tag="B-101",
        variable="presion_descarga",
        value=120,
        context={"reason": "Valor superior al límite"},
    )


def _order(status=OrderStatus.PENDING) -> Order:
    return Order(
        event_id=uuid4(),
        equipment_tag="B-101",
        task="T-B-EMP",
        parts=["EMP-1"],
        total_cost_usd=100,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=False,
        status=status,
        approval_reasons=["La tarea requiere contratista"],
    )


def test_state_message_matches_contract():
    payload = state_message("planta-test", False, 2)
    planta_contrato.EstadoSistema.model_validate(payload)
    assert payload["sistema"] == "planta-test"
    assert payload["enlace_ok"] is False
    assert payload["pendientes_sincronizar"] == 2


def test_event_message_matches_contract():
    event = _event()
    payload = event_message(event, nota_ids=["VIVO-1"])
    planta_contrato.EventoSistema.model_validate(payload)
    assert payload["tipo"] == "Escalado"
    assert payload["origen"] == "parte"
    assert payload["equipo"] == "B-101"
    assert payload["nota_ids"] == ["VIVO-1"]


def test_alert_message_matches_contract():
    alert = SafetyAlert(code="S1", message="Proyección de agua", source_id="part-1:safety:S1")
    payload = alert_message(alert, equipo="B-101", parte_id="part-1", nota_ids=["VIVO-1"])
    planta_contrato.EventoSistema.model_validate(payload)
    assert payload["tipo"] == "AlertaSeguridad"
    assert payload["equipo"] == "B-101"


def test_order_message_matches_contract():
    payload = order_message(_order())
    planta_contrato.OrdenSistema.model_validate(payload)
    assert payload["estado"] == "PendienteAprobacion"
    assert payload["ejecutor"] == "contratista"
    assert payload["repuestos"] == [{"codigo": "EMP-1", "cantidad": 1.0}]


def test_tablet_message_matches_contract():
    row = FilaParte(
        equipment_tag="B-101",
        variable="presion_descarga",
        value=110,
        unit="kg/cm2",
        observed_at=datetime.now(UTC),
    )
    payload = tablet_message(
        message_id="TAB-1",
        note_ids=["VIVO-1"],
        texto="¿Confirmás el parte?",
        filas=[row],
    )
    planta_contrato.MensajeTablet.model_validate(payload)
    assert payload["pantalla"]["filas"][0]["tag"] == "B-101"


def test_sensor_reading_from_contract():
    reading = sensor_reading_from_contract(
        {
            "tag": "B-101",
            "variable": "presion_descarga",
            "valor": 120.5,
            "unidad": "kg/cm2",
            "ts": "2026-11-05T10:00:00Z",
            "calidad": "buena",
        }
    )
    assert reading is not None
    assert reading.equipment_tag == "B-101"
    assert reading.value == 120.5
    assert reading.idempotency_key.startswith("sensor:B-101:presion_descarga:")
    assert (
        sensor_reading_from_contract(
            {
                "tag": "B-101",
                "variable": "presion_descarga",
                "valor": 120.5,
                "unidad": "kg/cm2",
                "ts": "2026-11-05T10:00:00Z",
                "calidad": "sin_dato",
            }
        )
        is None
    )


def test_bridge_publishes_contract_topics():
    from app.mqtt_bridge import MqttBridge

    fake = FakeMqtt()
    bridge = MqttBridge(
        on_recorrida=lambda _payload: None,
        on_sensor=lambda _payload: None,
        on_cierre=lambda _payload: None,
        on_respuesta=lambda _payload: None,
        client=fake,
    )
    bridge.start()
    bridge.publish_event(event_message(_event()))
    bridge.publish_order(order_message(_order()))
    bridge.publish_tablet({"id": "TAB-1"})
    bridge.publish_heartbeat("planta-test", True, 0)
    topics = [call[0][0] for call in fake.published]
    assert topics == [
        "sistema/eventos",
        "sistema/ordenes",
        "sistema/tablet",
        "sistema/estado",
    ]
    for call in fake.published:
        json.loads(call[0][1])


def test_health_returns_contract_shape():
    response = client.get("/health")
    assert response.status_code == 200
    planta_contrato.EstadoSistema.model_validate(response.json())


def test_equipment_from_definition():
    equipment = equipment_from_definition(
        {
            "equipos": [
                {
                    "tag": "B-101",
                    "tipo": "bomba",
                    "descripcion": "Bomba 1",
                    "nombres": ["la uno"],
                    "rol_inicial": "servicio",
                }
            ],
            "sensores": [
                {
                    "tag": "B-101",
                    "variable": "presion_descarga",
                    "alarma_baja": 95,
                    "alarma_alta": 125,
                }
            ],
        }
    )
    assert equipment[0].tag == "B-101"
    assert equipment[0].alarm_min == 95
    assert equipment[0].alarm_max == 125
    assert equipment[0].aliases == ["la uno"]


def test_sensor_callback_publishes_event(monkeypatch):
    class FakeBridge:
        def __init__(self):
            self.events = []

        def publish_event(self, payload):
            self.events.append(payload)

    fake_bridge = FakeBridge()
    service.__init__()
    service.add_equipment(
        Equipment(tag="B-101", name="Bomba 1", kind="bomba", alarm_max=125)
    )
    monkeypatch.setattr(main, "mqtt_bridge", fake_bridge)
    for value, ts in [(200, "2026-11-05T10:00:00Z"), (201, "2026-11-05T10:01:00Z")]:
        main._on_sensor(
            {
                "tag": "B-101",
                "variable": "presion_descarga",
                "valor": value,
                "unidad": "kg/cm2",
                "ts": ts,
                "calidad": "buena",
            }
        )
    assert len(fake_bridge.events) == 1
    planta_contrato.EventoSistema.model_validate(fake_bridge.events[0])
    assert fake_bridge.events[0]["tipo"] == "Escalado"
