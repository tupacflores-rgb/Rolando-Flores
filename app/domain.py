from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable
from uuid import UUID

from .models import (
    ClosureReport,
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


# Variables dichas en campo que se comparan contra el límite del sensor homónimo.
VARIABLE_LIMIT_MAP: dict[str, str] = {
    "presion_descarga_local": "presion_descarga",
    "presion_diferencial": "presion_diferencial",
}

# Observaciones de estado que no constituyen una anomalía.
NORMAL_OBSERVATIONS: frozenset[str] = frozenset(
    {"parada, en reserva", "parada por mantenimiento"}
)

# Estados de una bomba en los que no puede reemplazar a otra (reserva fuera de servicio).
RESERVE_UNAVAILABLE: frozenset[str] = frozenset(
    {"parada por mantenimiento", "disparada, no arranca"}
)


def evaluate_value(
    equipment: Equipment,
    value: float,
    *,
    variable: str | None = None,
    sustained: bool = True,
    state: str | None = None,
) -> Evaluation:
    if state and state.casefold() == "parada, en reserva":
        return Evaluation(EventStatus.NORMAL, "Equipo detenido en reserva: estado esperado")
    if not sustained:
        return Evaluation(EventStatus.NORMAL, "Pico aislado: requiere confirmación sostenida")
    limits = equipment.sensor_limits.get(variable or "") if variable else None
    alarm_min = limits.alarm_min if limits else equipment.alarm_min
    alarm_max = limits.alarm_max if limits else equipment.alarm_max
    if alarm_min is not None and value < alarm_min:
        return Evaluation(EventStatus.ESCALATED, "Valor inferior al límite de alarma")
    if alarm_max is not None and value > alarm_max:
        return Evaluation(EventStatus.ESCALATED, "Valor superior al límite de alarma")
    return Evaluation(EventStatus.NORMAL, "Valor dentro del rango de operación")


_SAFETY_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("S1", ("agua a presion", "proyeccion de agua", "chorro a presion"), "Alejarse y aislar la presión"),
    ("S2", ("olor a gas", "gas"), "Evacuar el área y avisar por radio"),
    ("S3", ("humo", "fuego", "incendio"), "Activar el procedimiento contra incendio"),
    ("S4", ("persona lesionada", "lesionado", "herido", "sangrando", "sangre",
            "golpeo la mano", "se golpeo", "se lastimo", "lastimado"), "Solicitar asistencia y asegurar el área"),
)


def detect_safety(text: str, source_id: str) -> list[SafetyAlert]:
    normalized = unicodedata.normalize("NFD", text.casefold())
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    normalized = re.sub(r"\s+", " ", normalized)
    alerts: list[SafetyAlert] = []
    for code, patterns, action in _SAFETY_PATTERNS:
        matched = False
        for pattern in patterns:
            found = re.search(rf"\b{re.escape(pattern)}\b", normalized)
            if found:
                prefix = normalized[max(0, found.start() - 16):found.start()]
                directly_negated = re.search(
                    rf"(?:\bno\s+(?:hay\s+)?|\bsin\s+){re.escape(pattern)}\s*$",
                    prefix + pattern,
                )
                if pattern == "gas" and re.search(
                    r"\b(?:no\s+(?:hay\s+)?|sin\s+)olor\s+a\s+gas\s*$",
                    prefix + pattern,
                ):
                    directly_negated = True
                if not directly_negated:
                    matched = True
                    break
        if matched:
            alerts.append(
                SafetyAlert(
                    code=code,
                    message=f"Condición insegura {code}: {action}",
                    source_id=source_id,
                )
            )
    return alerts


class DomainService:
    def __init__(self, repository=None) -> None:
        self.repository = repository
        self.equipment: dict[str, Equipment] = {}
        self.parts: dict[str, Part] = {}
        self.sensor_readings: dict[str, SensorReading] = {}
        self.events: dict[str, Event] = {}
        self.events_by_id: dict[str, Event] = {}
        self.alerts: dict[str, SafetyAlert] = {}
        self.orders: dict[str, Order] = {}
        self.inventory_catalog: list[dict] = []
        self.material_catalog: dict[str, list[dict]] = {}
        self.task_catalog: list[dict] = []
        self.manual_index = None
        self.tool_audits: list[dict] = []
        self.pump_states: dict[str, str] = {}
        self.sync_queue: deque[str] = deque()
        self.sync_items: dict[str, dict] = {}
        self._sustained: dict[tuple[str, str], list[tuple[datetime, float]]] = defaultdict(list)
        if self.repository:
            restored = self.repository.restore()
            self.equipment = {item.tag: item for item in restored["equipment"]}
            self.parts = {item.idempotency_key: item for item in restored["parts"]}
            restored_sensors = restored.get("sensor_readings", [])
            self.sensor_readings = {
                item.idempotency_key: item for item in restored_sensors
            }
            self.events = {item.idempotency_key: item for item in restored["events"]}
            self.events_by_id = {str(item.id): item for item in restored["events"]}
            self.alerts = {str(item.id): item for item in restored["alerts"]}
            self.orders = {str(item.id): item for item in restored["orders"]}
            for reading in restored_sensors:
                key = (reading.equipment_tag, reading.variable)
                self._sustained[key].append((self._aware(reading.observed_at), reading.value))
            for item in restored.get("sync", []):
                self.sync_items[item["idempotency_key"]] = item
                self.sync_queue.append(item["idempotency_key"])

    def get_event(self, event_id: str | UUID) -> Event | None:
        return self.events_by_id.get(str(event_id))

    def _remember_event(self, event: Event) -> None:
        self.events[event.idempotency_key] = event
        self.events_by_id[str(event.id)] = event

    def add_equipment(self, equipment: Equipment) -> Equipment:
        self.equipment[equipment.tag] = equipment
        if self.repository:
            self.repository.save_equipment(equipment)
        return equipment

    def confirm_part(self, key: str) -> Part:
        part = self.parts[key]
        part.status = part.status.CONFIRMED
        if self.repository:
            self.repository.save_part(part)
        return part

    def save_part(self, part: Part) -> Part:
        existing = self.parts.get(part.idempotency_key)
        if existing:
            if existing.model_dump(exclude={"status", "id"}) != part.model_dump(
                exclude={"status", "id"}
            ):
                raise ValueError("La clave idempotente ya existe con otro payload")
            return existing
        self.parts[part.idempotency_key] = part
        if self.repository:
            self.repository.save_part(part)
        return part

    def attach_closure(self, order_id: str, closure: ClosureReport) -> Order:
        order = self.orders[order_id]
        order.closure = closure
        if self.repository:
            self.repository.save_order(order)
        return order

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
                if self.repository:
                    self.repository.save_alert(alert)
                existing_alert = alert
            results.append(existing_alert)

        # Una decisión por equipo: cualquier lectura anómala (valor fuera de límite u
        # observación que no es un estado normal) escala el equipo; si no, Sin novedad.
        per_tag: dict[str, dict] = {}
        for reading in part.readings:
            equipment = self.equipment.get(reading.equipment_tag)
            if equipment is None:
                raise ValueError(f"Equipo inexistente: {reading.equipment_tag}")
            if reading.variable == "estado" and reading.observation:
                # La recorrida reporta el estado de la bomba; actualiza la disponibilidad dinámica.
                self.pump_states[reading.equipment_tag] = reading.observation
            entry = per_tag.setdefault(
                reading.equipment_tag,
                {"anomalous": False, "variable": None, "value": None, "photos": [], "has_content": False},
            )
            observation = (reading.observation or "").strip()
            if observation:
                entry["has_content"] = True
                if (
                    observation.casefold() not in NORMAL_OBSERVATIONS
                    and not detect_safety(observation, str(part.id))
                ):
                    entry["anomalous"] = True
            if reading.value is not None:
                entry["has_content"] = True
                entry["variable"] = entry["variable"] or reading.variable
                entry["value"] = reading.value
                limit_variable = VARIABLE_LIMIT_MAP.get(reading.variable, reading.variable)
                limits = equipment.sensor_limits.get(limit_variable)
                if limits is not None:
                    if limits.alarm_min is not None and reading.value < limits.alarm_min:
                        entry["anomalous"] = True
                    if limits.alarm_max is not None and reading.value > limits.alarm_max:
                        entry["anomalous"] = True
            entry["photos"].extend(reading.photo_ids)

        for tag, entry in per_tag.items():
            if not entry["has_content"]:
                continue
            status = EventStatus.ESCALATED if entry["anomalous"] else EventStatus.NORMAL
            event_key = f"part:{part.idempotency_key}:{tag}"
            if event_key in self.events:
                results.append(self.events[event_key])
                continue
            reason = (
                "Anomalía en la recorrida" if entry["anomalous"]
                else "Valor dentro del rango de operación"
            )
            event = Event(
                idempotency_key=event_key,
                origin="part",
                source_id=str(part.id),
                status=status,
                equipment_tag=tag,
                variable=entry["variable"],
                value=entry["value"],
                context={"reason": reason, "photos": list(dict.fromkeys(entry["photos"]))},
            )
            self._remember_event(event)
            if self.repository:
                self.repository.save_event(event)
            results.append(event)
        return results

    def evaluate_sensor(self, reading: SensorReading, sustained: bool = False) -> Event:
        if reading.idempotency_key in self.events:
            previous = self.sensor_readings.get(reading.idempotency_key)
            if previous and previous != reading:
                raise ValueError("La clave idempotente ya existe con otra lectura")
            return self.events[reading.idempotency_key]
        equipment = self.equipment.get(reading.equipment_tag)
        if equipment is None:
            raise ValueError(f"Equipo inexistente: {reading.equipment_tag}")
        key = (equipment.tag, reading.variable)
        observed_at = self._aware(reading.observed_at)
        history = self._sustained[key]
        history.append((observed_at, reading.value))
        cutoff = observed_at - timedelta(hours=4)
        self._sustained[key] = [(when, val) for when, val in history if when >= cutoff]
        anomalies = [
            val for _, val in self._sustained[key]
            if (
                (limits := equipment.sensor_limits.get(reading.variable)) is not None
                and (
                    (limits.alarm_min is not None and val < limits.alarm_min)
                    or (limits.alarm_max is not None and val > limits.alarm_max)
                )
            )
            or (
                limits is None
                and (
                    (equipment.alarm_min is not None and val < equipment.alarm_min)
                    or (equipment.alarm_max is not None and val > equipment.alarm_max)
                )
            )
        ]
        sustained = sustained or len(anomalies) >= 2
        evaluation = evaluate_value(
            equipment, reading.value, variable=reading.variable, sustained=sustained
        )
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
        self._remember_event(event)
        self.sensor_readings[reading.idempotency_key] = reading
        if self.repository:
            self.repository.save_sensor(reading)
            self.repository.save_event(event)
        return event

    def _ensure_order_for_event(self, event: Event) -> Order:
        existing = next(
            (order for order in self.orders.values() if order.event_id == event.id),
            None,
        )
        if existing is not None:
            return existing
        open_order = next(
            (
                order
                for order in self.orders.values()
                if order.equipment_tag == event.equipment_tag
                and order.status
                not in {
                    OrderStatus.REJECTED,
                    OrderStatus.CLOSED,
                    OrderStatus.CERTIFIED,
                }
            ),
            None,
        )
        if open_order is not None:
            return open_order
        task = "I-VIB" if event.variable == "vibracion" else "I-VAL"
        order = Order(
            event_id=event.id,
            equipment_tag=event.equipment_tag,
            task=task,
            total_cost_usd=0,
            stock_available=False,
            standard_task=False,
            keeps_injection=False,
            internal_staff=False,
            structural_damage=False,
            detiene_equipo=True,
            reduce_inyeccion=True,
            evidence={
                "event_id": str(event.id),
                "variable": event.variable,
                "value": event.value,
                "context": event.context,
            },
        )
        return self.create_order(order)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return value

    def _reserve_available(self, target: Equipment | None) -> bool:
        """Reserva disponible para reemplazar a ``target``, según el estado reportado.

        Una bomba de reserva en ``parada por mantenimiento`` o ``disparada, no
        arranca`` no puede reemplazar a nadie, aunque su rol inicial sea reserva.
        """
        if target is None:
            return False
        for item in self.equipment.values():
            if item.tag == target.tag or item.kind != target.kind:
                continue
            if not item.reserve_available:
                continue
            state = self.pump_states.get(item.tag)
            if state and state.casefold() in RESERVE_UNAVAILABLE:
                continue
            return True
        return False

    def create_order(self, request: Order) -> Order:
        existing = next((o for o in self.orders.values() if o.event_id == request.event_id), None)
        if existing:
            return existing
        reasons: list[str] = []
        catalog_task = None
        official_equipment = {
            equipment
            for task in self.task_catalog
            for equipment in task.get("equipos", [])
        }
        official_equipment.update(self.equipment)
        if self.task_catalog and request.equipment_tag in official_equipment:
            task_text = request.task.casefold()
            catalog_task = next(
                (
                    task
                    for task in self.task_catalog
                    if (
                        str(task.get("codigo", "")).casefold() == task_text
                        or str(task.get("nombre", "")).casefold() == task_text
                    )
                    and (
                        not task.get("equipos")
                        or request.equipment_tag in task.get("equipos", [])
                    )
                ),
                None,
            )
            if catalog_task is None:
                reasons.append("La tarea no está en el catálogo oficial para ese equipo")
                request.parts = []
            else:
                request.task = str(catalog_task["nombre"])
                request.standard_task = bool(catalog_task.get("estandar", True))
                request.detiene_equipo = bool(catalog_task.get("detiene", False))
                target = self.equipment.get(request.equipment_tag)
                reserve_available = self._reserve_available(target)
                request.keeps_injection = (
                    not request.detiene_equipo or reserve_available
                )
                request.internal_staff = catalog_task.get("ejecutor") == "propio"
                required = {
                    part["codigo"]: float(part.get("cantidad", 0))
                    for part in catalog_task.get("repuestos", [])
                }
                request.parts = list(required)
                prices = {
                    item.get("codigo"): float(item.get("costo_usd", 0))
                    for item in self.inventory_catalog
                }
                stock = {
                    item.get("codigo"): float(
                        item.get("stock", {}).get("yacimiento", 0)
                    )
                    for item in self.inventory_catalog
                }
                for code, quantity in required.items():
                    if code not in prices:
                        reasons.append(f"Repuesto sin precio oficial: {code}")
                    if code not in stock:
                        reasons.append(f"Repuesto sin stock oficial: {code}")
                    elif stock[code] < quantity:
                        reasons.append(
                            f"Stock insuficiente para {code}: "
                            f"requiere {quantity}, disponible {stock[code]}"
                        )
                request.total_cost_usd = sum(
                    quantity * prices.get(code, 0)
                    for code, quantity in required.items()
                )
                request.stock_available = not any(
                    code not in stock or stock[code] < quantity
                    for code, quantity in required.items()
                )
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
        if self.repository:
            self.repository.save_order(request)
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
        if self.repository:
            self.repository.save_order(order)
        return order

    def enqueue(self, operation: str, key: str, payload: dict) -> dict:
        if key in self.sync_items:
            item = self.sync_items[key]
            if not item["synced"]:
                item.update(operation=operation, payload=payload, last_error=None)
                if self.repository:
                    self.repository.save_sync(item)
            return item
        item = {"idempotency_key": key, "operation": operation, "payload": payload, "attempts": 0, "synced": False}
        self.sync_items[key] = item
        self.sync_queue.append(key)
        if self.repository:
            self.repository.save_sync(item)
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
                if self.repository:
                    self.repository.save_sync(item)
                break
            item["synced"] = True
            self.sync_queue.remove(key)
            if self.repository:
                self.repository.save_sync(item)
            completed.append(item)
        return completed
