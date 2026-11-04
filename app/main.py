from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, status

from .domain import DomainService
from .models import (
    Equipment,
    Event,
    EventStatus,
    Order,
    OrderCreate,
    OrderStatus,
    Part,
    PartCreate,
    SafetyAlert,
    SensorReading,
)
from .tools import EquipmentQuery, ReadOnlyTools, SensorHistoryQuery

app = FastAPI(title="Planta de inyección de agua", version="0.1.0")
service = DomainService()
tools = ReadOnlyTools(service)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "sistema": "planta", "enlace_ok": False, "pendientes_sincronizar": len(service.sync_queue)}


@app.post("/api/equipos", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(equipment: Equipment) -> Equipment:
    return service.add_equipment(equipment)


@app.get("/api/equipos", response_model=list[Equipment])
def list_equipment(tag: str | None = None) -> list[Equipment]:
    return tools.equipment(EquipmentQuery(tag=tag))


@app.post("/api/partes", response_model=Part, status_code=status.HTTP_201_CREATED)
def create_part(request: PartCreate) -> Part:
    return service.save_part(Part(**request.model_dump()))


@app.post("/api/partes/{idempotency_key}/confirmar", response_model=list[Event | SafetyAlert])
def confirm_part(idempotency_key: str) -> list[Event | SafetyAlert]:
    try:
        part = service.confirm_part(idempotency_key)
        return service.evaluate_part(part)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Parte inexistente") from exc


@app.post("/api/sensores", response_model=Event)
def ingest_sensor(reading: SensorReading) -> Event:
    try:
        return service.evaluate_sensor(reading)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/eventos", response_model=list[Event])
def list_events() -> list[Event]:
    return list(service.events.values())


@app.get("/api/alertas-seguridad", response_model=list[SafetyAlert])
def list_alerts() -> list[SafetyAlert]:
    return list(service.alerts.values())


@app.post("/api/ordenes", response_model=Order)
def create_order(request: OrderCreate) -> Order:
    return service.create_order(Order(**request.model_dump()))


@app.post("/api/ordenes/{order_id}/transicion", response_model=Order)
def transition_order(order_id: str, target: OrderStatus, reason: str | None = None) -> Order:
    try:
        return service.transition_order(order_id, target, reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Orden inexistente") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/ordenes", response_model=list[Order])
def list_orders() -> list[Order]:
    return list(service.orders.values())


@app.get("/api/tools/equipos", response_model=list[Equipment])
def tool_equipment(tag: str | None = None) -> list[Equipment]:
    return tools.equipment(EquipmentQuery(tag=tag))


@app.get("/api/tools/sensores")
def tool_sensor_history(tag: str, variable: str, limit: int = 100) -> list[dict[str, Any]]:
    return tools.sensor_history(SensorHistoryQuery(tag=tag, variable=variable, limit=limit))


@app.get("/api/sincronizacion/pendientes")
def pending_sync() -> list[dict]:
    return [service.sync_items[key] for key in service.sync_queue]


@app.post("/api/sincronizacion/encolar")
def enqueue_sync(operation: str, idempotency_key: str, payload: dict[str, Any]) -> dict:
    return service.enqueue(operation, idempotency_key, payload)


@app.post("/api/sincronizacion/procesar")
def process_sync(enlace_ok: bool = False) -> list[dict]:
    if not enlace_ok:
        return []
    return service.sync(lambda item: None)
