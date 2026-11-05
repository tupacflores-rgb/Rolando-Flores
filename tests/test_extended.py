from datetime import datetime, timedelta

import pytest

from app.certification import compare_closure, issue_habilita
from app.integrations import VoicePartExtractor
from app.memory import ConversationMemory
from app.mqtt_bridge import MqttBridge
from app.models import (
    ClosureReport,
    Equipment,
    ManualChunk,
    Order,
    RetrievalQuery,
    VoiceNote,
)
from app.rag import ManualIndex
from app.official_data import load_equipment


def test_voice_extractor_keeps_note_timestamp_and_photo():
    equipment = Equipment(
        tag="B-101",
        name="Bomba 1",
        aliases=["la uno"],
        kind="bomba",
    )
    note = VoiceNote(
        note_id="VIVO-1",
        observed_at=datetime(2026, 11, 5, 10, 0),
        photo_urls=["foto-1"],
    )
    rows = VoicePartExtractor([equipment]).extract(note, "La uno está en 112 kilos")
    assert rows[0].observed_at == note.observed_at
    assert rows[0].unit == "kg/cm2"
    assert rows[0].photo_ids == ["foto-1"]


def test_official_plant_data_and_spanish_number_are_supported():
    equipment = load_equipment(
        r"C:\Users\Rolando\Documents\GitHub\academia2026-tp\datos\planta.yaml"
    )
    note = VoiceNote(note_id="NOTA-00004", observed_at=datetime(2026, 11, 5, 10, 0))
    rows = VoicePartExtractor(equipment).extract(
        note, "La del medio está en mil seiscientos cuarenta psi de descarga"
    )
    assert rows[0].equipment_tag == "B-102"
    assert rows[0].value == 1640
    assert rows[0].unit == "psi"
    assert next(item for item in equipment if item.tag == "B-101").alarm_max == 125


def test_voice_extractor_uses_official_aliases():
    equipment = load_equipment(
        r"C:\Users\Rolando\Documents\GitHub\academia2026-tp\datos\planta.yaml"
    )
    note = VoiceNote(note_id="VIVO-3", observed_at=datetime(2026, 11, 5, 10, 0))
    rows = VoicePartExtractor(equipment).extract(
        note, "El de la izquierda está en dieciocho psi"
    )
    assert rows[0].equipment_tag == "F-201A"


def test_voice_extractor_rejects_ambiguous_alias():
    equipment = [
        Equipment(tag="B-101", name="Bomba 1", aliases=["la bomba"], kind="bomba"),
        Equipment(tag="B-102", name="Bomba 2", aliases=["la bomba"], kind="bomba"),
    ]
    with pytest.raises(ValueError, match="ambiguo"):
        VoicePartExtractor(equipment).extract(
            VoiceNote(note_id="VIVO-2", observed_at=datetime.utcnow()),
            "La bomba está en 100 kilos",
        )


def test_rag_filters_expired_chunks_and_keeps_citation():
    index = ManualIndex(
        [
            ManualChunk(
                equipment_tag="B-101",
                manufacturer="Acme",
                document="TX350-D",
                section="§3.2",
                citation="TX350-D §3.2",
                text="presión de descarga máxima",
            ),
            ManualChunk(
                equipment_tag="B-101",
                manufacturer="Acme",
                document="TX350-C",
                section="§3.2",
                citation="TX350-C §3.2",
                text="presión de descarga máxima",
                vigente=False,
            ),
        ]
    )
    results = index.search(RetrievalQuery(question="presión máxima", equipment_tag="B-101"))
    assert len(results) == 1
    assert results[0].chunk.citation == "TX350-D §3.2"


def test_closure_uses_contract_price_not_declared_amount():
    order = Order(
        event_id=__import__("uuid").uuid4(),
        equipment_tag="B-101",
        task="cambiar empaquetadura",
        parts=["EMP-1"],
        total_cost_usd=9999,
        stock_available=True,
        standard_task=True,
        keeps_injection=True,
        internal_staff=False,
    )
    closure = ClosureReport(
        order_id=order.id,
        technician="contratista",
        contractor=True,
        tasks_done=["cambiar empaquetadura"],
        parts_used=["EMP-1"],
        hours=2,
        final_test="110 kilos sin pérdida",
    )
    assert compare_closure(order, closure).matches
    assert issue_habilita(order, {"EMP-1": 125}).amount_usd == 125


def test_memory_purges_old_conversation():
    memory = ConversationMemory(retention_days=45)
    memory.append("VIVO-1", "nota", {"text": "ok"})
    assert len(memory.get("VIVO-1")) == 1
    old = datetime.utcnow() + timedelta(days=46)
    assert memory.purge(old) == 1


class FakeMqtt:
    def __init__(self):
        self.published = []
        self.subscriptions = []
        self.on_message = None

    def connect(self, *_args, **_kwargs):
        return None

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


def test_official_mqtt_contract_heartbeat():
    client = FakeMqtt()
    bridge = MqttBridge(
        on_recorrida=lambda _payload: None,
        on_sensor=lambda _payload: None,
        on_cierre=lambda _payload: None,
        on_respuesta=lambda _payload: None,
        client=client,
    )
    bridge.start()
    bridge.publish_heartbeat("planta-test", False, 2)
    assert len(client.subscriptions) == 4
    assert client.published[0][0][0] == "sistema/estado"
