from __future__ import annotations

from typing import Protocol

from .models import Equipment, Event, Order, Part, SafetyAlert, SensorReading


class Repository(Protocol):
    def save_part(self, part: Part) -> Part: ...
    def save_sensor(self, reading: SensorReading) -> SensorReading: ...
    def save_event(self, event: Event) -> Event: ...
    def save_alert(self, alert: SafetyAlert) -> SafetyAlert: ...
    def save_order(self, order: Order) -> Order: ...
    def list_equipment(self) -> list[Equipment]: ...


class MemoryRepository:
    def __init__(self) -> None:
        self.parts: dict[str, Part] = {}
        self.sensors: dict[str, SensorReading] = {}
        self.events: dict[str, Event] = {}
        self.alerts: dict[str, SafetyAlert] = {}
        self.orders: dict[str, Order] = {}
        self.equipment: dict[str, Equipment] = {}

    def save_part(self, part: Part) -> Part:
        return self.parts.setdefault(part.idempotency_key, part)

    def save_sensor(self, reading: SensorReading) -> SensorReading:
        return self.sensors.setdefault(reading.idempotency_key, reading)

    def save_event(self, event: Event) -> Event:
        return self.events.setdefault(event.idempotency_key, event)

    def save_alert(self, alert: SafetyAlert) -> SafetyAlert:
        self.alerts.setdefault(str(alert.id), alert)
        return alert

    def save_order(self, order: Order) -> Order:
        self.orders.setdefault(str(order.id), order)
        return order

    def list_equipment(self) -> list[Equipment]:
        return list(self.equipment.values())

