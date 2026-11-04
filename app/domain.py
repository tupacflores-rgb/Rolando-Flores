from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .models import (
    Equipment,
    Event,
    EventStatus,
    Order,
    OrderStatus,
    Part,
    SafetyAlert,
    SensorReading,
)


@dataclass(frozen=True)
class Evaluation:
    status: EventStatus
    reason: str


def evaluate_value(
    equipment: Equipment,
    value: float,
    *,
    sustained: bool = True,
    state: str | None = None,
) -> Evaluation:
    if state and state.casefold() == "parada, en reserva":
        return Evaluation(EventStatus.NORMAL, "Equipo detenido en reserva: estado esperado")
    if not sustained:
        return Evaluation(EventStatus.NORMAL, "Pico aislado: requiere confirmación sostenida")
    if equipment.alarm_min is not None and value < equipment.alarm_min:
        return Evaluation(EventStatus.ESCALATED, "Valor inferior al límite de alarma")
    if equipment.alarm_max is not None and value > equipment.alarm_max:
        return Evaluation(EventStatus.ESCALATED, "Valor superior al límite de alarma")
    return Evaluation(EventStatus.NORMAL, "Valor dentro del rango de operación")


_SAFETY_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("S1", ("agua a presión", "proyección de agua", "chorro a presión"), "Alejarse y aislar la presión"),
    ("S2", ("olor a gas", "gas"), "Evacuar el área y avisar por radio"),
    ("S3", ("humo", "fuego", "incendio"), "Activar el procedimiento contra incendio"),
    ("S4", ("persona lesionada", "lesionado", "herido"), "Solicitar asistencia y asegurar el área"),
)


def detect_safety(text: str, source_id: str) -> list[SafetyAlert]:
    normalized = re.sub(r"\s+", " ", text.casefold())
    alerts: list[SafetyAlert] = []
    for code, patterns, action in _SAFETY_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            alerts.append(
                SafetyAlert(
                    code=code,
                    message=f"Condición insegura {code}: {action}",
                    source_id=source_id,
                )
            )
    return alerts


class DomainService:
    def __init__(self) -> None:
        self.equipment: dict[str, Equipment] = {}
        self.parts: dict[str, Part] = {}
        self.sensor_readings: dict[str, SensorReading] = {}
        self.events: dict[str, Event] = {}
        self.alerts: dict[str, SafetyAlert] = {}
        self.orders: dict[str, Order] = {}
        self.sync_queue: deque[str] = deque()
        self.sync_items: dict[str, dict] = {}
        self._sustained: dict[tuple[str, str], list[tuple[datetime, float]]] = defaultdict(list)

    def add_equipment(self, equipment: Equipment) -> Equipment:
        self.equipment[equipment.tag] = equipment
        return equipment

    def confirm_part(self, key: str) -> Part:
        part = self.parts[key]
        part.status = part.status.CONFIRMED
        return part

    def save_part(self, part: Part) -> Part:
        existing = self.parts.get(part.idempotency_key)
        if existing:
            return existing
        self.parts[part.idempotency_key] = part
        return part

    def evaluate_part(self, part: Part) -> list[Event | SafetyAlert]:
        if part.status != part.status.CONFIRMED:
            raise ValueError("Solo un parte confirmado genera eventos")
        results: list[Event | SafetyAlert] = []
        text = " ".join(
            filter(
                None,
                (reading.observation or "" for reading in part.readings),
            )
        )
        for alert in detect_safety(text, str(part.id)):
            alert_key = f"{part.id}:safety:{alert.code}"
            existing_alert = next(
                (saved for saved in self.alerts.values() if saved.source_id == alert_key),
                None,
            )
            if existing_alert is None:
                alert.source_id = alert_key
                self.alerts[str(alert.id)] = alert
                existing_alert = alert
            results.append(existing_alert)
        for index, reading in enumerate(part.readings):
            equipment = self.equipment.get(reading.equipment_tag)
            if equipment is None:
                raise ValueError(f"Equipo inexistente: {reading.equipment_tag}")
            if reading.value is None:
                continue
            key = (equipment.tag, reading.variable)
            history = self._sustained[key]
            history.append((part.observed_at, reading.value))
            cutoff = part.observed_at - timedelta(hours=4)
            self._sustained[key] = [(when, val) for when, val in history if when >= cutoff]
            sustained = len(self._sustained[key]) >= 2
            result = evaluate_value(equipment, reading.value, sustained=sustained)
            event_key = f"part:{part.idempotency_key}:{index}"
            if event_key in self.events:
                results.append(self.events[event_key])
                continue
            event = Event(
                idempotency_key=event_key,
                origin="part",
                source_id=str(part.id),
                status=result.status,
                equipment_tag=equipment.tag,
                variable=reading.variable,
                value=reading.value,
                context={"reason": result.reason, "photos": reading.photo_ids},
            )
            self.events[event_key] = event
            results.append(event)
        return results

    def evaluate_sensor(self, reading: SensorReading, sustained: bool = True) -> Event:
        if reading.idempotency_key in self.events:
            return self.events[reading.idempotency_key]
        equipment = self.equipment.get(reading.equipment_tag)
        if equipment is None:
            raise ValueError(f"Equipo inexistente: {reading.equipment_tag}")
        key = (equipment.tag, reading.variable)
        self._sustained[key].append((reading.observed_at, reading.value))
        evaluation = evaluate_value(equipment, reading.value, sustained=sustained)
        event = Event(
            idempotency_key=reading.idempotency_key,
            origin="sensor",
            source_id=reading.idempotency_key,
            status=evaluation.status,
            equipment_tag=equipment.tag,
            variable=reading.variable,
            value=reading.value,
            context={"reason": evaluation.reason},
        )
        self.events[reading.idempotency_key] = event
        return event

    def create_order(self, request: Order) -> Order:
        existing = next((o for o in self.orders.values() if o.event_id == request.event_id), None)
        if existing:
            return existing
        reasons: list[str] = []
        if not request.standard_task:
            reasons.append("La tarea no está en el catálogo estándar")
        if not request.keeps_injection:
            reasons.append("La inyección no se mantiene")
        if not request.stock_available:
            reasons.append("Faltan repuestos en stock")
        if request.total_cost_usd >= 2500:
            reasons.append("El costo debe ser menor a USD 2.500")
        if not request.internal_staff:
            reasons.append("La tarea requiere contratista")
        if request.structural_damage:
            reasons.append("Daño estructural grave: revisión humana obligatoria")
        request.approval_reasons = reasons
        request.status = OrderStatus.APPROVED if not reasons else OrderStatus.PENDING
        self.orders[str(request.id)] = request
        return request

    def transition_order(self, order_id: str, target: OrderStatus, reason: str | None = None) -> Order:
        order = self.orders[order_id]
        allowed = {
            OrderStatus.DRAFT: {OrderStatus.PENDING, OrderStatus.APPROVED, OrderStatus.REJECTED},
            OrderStatus.PENDING: {OrderStatus.APPROVED, OrderStatus.REJECTED},
            OrderStatus.APPROVED: {OrderStatus.EXECUTED},
            OrderStatus.EXECUTED: {OrderStatus.CLOSED, OrderStatus.OBSERVED, OrderStatus.CERTIFIED},
            OrderStatus.OBSERVED: {OrderStatus.EXECUTED},
        }
        if target not in allowed.get(order.status, set()):
            raise ValueError(f"Transición inválida: {order.status} -> {target}")
        order.status = target
        if reason:
            order.approval_reasons.append(reason)
        return order

    def enqueue(self, operation: str, key: str, payload: dict) -> dict:
        if key in self.sync_items:
            return self.sync_items[key]
        item = {"idempotency_key": key, "operation": operation, "payload": payload, "attempts": 0, "synced": False}
        self.sync_items[key] = item
        self.sync_queue.append(key)
        return item

    def sync(self, publish) -> list[dict]:
        completed: list[dict] = []
        for key in list(self.sync_queue):
            item = self.sync_items[key]
            if item["synced"]:
                self.sync_queue.remove(key)
                continue
            item["attempts"] += 1
            try:
                publish(item)
            except Exception as exc:
                item["last_error"] = str(exc)
                break
            item["synced"] = True
            self.sync_queue.remove(key)
            completed.append(item)
        return completed
