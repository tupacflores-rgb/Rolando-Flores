from datetime import datetime
from uuid import uuid4

import pytest

from app.domain import DomainService, detect_safety, evaluate_value
from app.models import (
    Equipment,
    EventStatus,
    Order,
    OrderStatus,
    Part,
    PartReading,
    SensorReading,
)


def pump(**overrides):
    return Equipment(
        tag="B-101",
        name="Bomba 1",
        aliases=["la uno", "la bomba 1"],
        kind="bomba",
        alarm_max=110,
        reserve_available=False,
        **overrides,
    )


def test_normal_value_is_terminal():
    assert evaluate_value(pump(), 100).status == EventStatus.NORMAL


def test_anomaly_requires_sustained_signal():
    assert evaluate_value(pump(), 120, sustained=False).status == EventStatus.NORMAL
    assert evaluate_value(pump(), 120, sustained=True).status == EventStatus.ESCALATED


def test_part_is_idempotent_and_safety_is_local():
    service = DomainService()
    service.add_equipment(pump())
    part = Part(
        idempotency_key="p-1",
        operator_id="op",
        observed_at=datetime.utcnow(),
        readings=[
            PartReading(
                equipment_tag="B-101",
                variable="presion_descarga",
                value=100,
                unit="kg/cm2",
                observation="olor a gas",
            )
        ],
    )
    service.save_part(part)
    service.confirm_part("p-1")
    first = service.evaluate_part(part)
    second = service.evaluate_part(part)
    assert len([item for item in first if hasattr(item, "code")]) == 1
    assert [item.id for item in first if hasattr(item, "id")] == [item.id for item in second if hasattr(item, "id")]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"standard_task": True, "keeps_injection": True, "stock_available": True, "internal_staff": True, "total_cost_usd": 100}, OrderStatus.APPROVED),
        ({"standard_task": False, "keeps_injection": True, "stock_available": True, "internal_staff": True, "total_cost_usd": 100}, OrderStatus.PENDING),
        ({"standard_task": True, "keeps_injection": True, "stock_available": True, "internal_staff": True, "total_cost_usd": 2500}, OrderStatus.PENDING),
    ],
)
def test_order_rules(kwargs, expected):
    service = DomainService()
    order = Order(event_id=uuid4(), equipment_tag="B-101", task="inspeccion", parts=[], **kwargs)
    assert service.create_order(order).status == expected


def test_offline_queue_retries_in_order_without_duplicates():
    service = DomainService()
    service.enqueue("event", "e-1", {"value": 1})
    service.enqueue("event", "e-1", {"value": 1})
    published = []
    assert len(service.sync_queue) == 1
    service.sync(lambda item: published.append(item["idempotency_key"]))
    assert published == ["e-1"]
    assert service.sync_items["e-1"]["synced"] is True


def test_fuga_sin_enlace_creates_local_alert():
    service = DomainService()
    service.add_equipment(pump())
    part = Part(
        idempotency_key="leak-offline",
        operator_id="op",
        observed_at=datetime.utcnow(),
        readings=[
            PartReading(
                equipment_tag="B-101",
                variable="presion_descarga",
                value=100,
                unit="kg/cm2",
                observation="pérdida con proyección de agua a presión",
            )
        ],
    )
    service.save_part(part)
    service.confirm_part("leak-offline")
    results = service.evaluate_part(part)
    alerts = [item for item in results if hasattr(item, "code")]
    assert alerts and alerts[0].code == "S1"
    assert not service.sync_queue


def test_sustained_requires_two_anomalous_readings():
    service = DomainService()
    service.add_equipment(pump())
    first = service.evaluate_sensor(
        SensorReading(
            idempotency_key="s-1",
            equipment_tag="B-101",
            variable="presion",
            value=120,
            unit="kg/cm2",
            observed_at=datetime.utcnow(),
        )
    )
    second = service.evaluate_sensor(
        SensorReading(
            idempotency_key="s-2",
            equipment_tag="B-101",
            variable="presion",
            value=121,
            unit="kg/cm2",
            observed_at=datetime.utcnow(),
        )
    )
    assert first.status == EventStatus.NORMAL
    assert second.status == EventStatus.ESCALATED


def test_safety_negation_and_accents_do_not_false_alarm():
    assert detect_safety("No hay olor a gas y la presión es normal", "x") == []
    assert detect_safety("Pérdida con proyección de agua a presión", "x")[0].code == "S1"
