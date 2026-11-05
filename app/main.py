from __future__ import annotations

from datetime import datetime
import os
from typing import Any

from fastapi import FastAPI, HTTPException, status

from .domain import DomainService
from .certification import compare_closure, issue_habilita
from .integrations import VoicePartExtractor, apply_tablet_response
from .memory import ConversationMemory
from .persistence import build_repository
from .models import (
    ClosureReport,
    ClosureComparison,
    Equipment,
    Event,
    EventStatus,
    FilaParte,
    Order,
    OrderCreate,
    OrderStatus,
    Part,
    PartCreate,
    SafetyAlert,
    SensorReading,
    TabletResponse,
    VoiceNote,
)
from .tools import EquipmentQuery, ReadOnlyTools, SensorHistoryQuery

app = FastAPI(title="Planta de inyección de agua", version="0.1.0")
database_url = os.path.expandvars(os.getenv("DATABASE_URL", ""))
repository = build_repository(database_url)
service = DomainService(repository=repository)
tools = ReadOnlyTools(service)
memory = ConversationMemory()
draft_rows: dict[str, list[FilaParte]] = {}
closures: dict[str, ClosureReport] = {}


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


@app.post("/api/recorridas/procesar", response_model=list[FilaParte])
def process_voice_note(note: VoiceNote) -> list[FilaParte]:
    if not note.transcript:
        raise HTTPException(
            status_code=422,
            detail="La nota requiere transcript o un transcriptor local configurado",
        )
    try:
        rows = VoicePartExtractor(list(service.equipment.values())).extract(
            note, note.transcript
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    draft_rows[note.note_id] = rows
    memory.append(note.note_id, "nota", note.model_dump(mode="json"))
    memory.append(note.note_id, "borrador", {"filas": [row.model_dump() for row in rows]})
    return rows


@app.post("/api/tablet/respuesta", response_model=list[FilaParte])
def process_tablet_response(response: TabletResponse) -> list[FilaParte]:
    rows = draft_rows.get(response.note_id)
    if rows is None:
        raise HTTPException(status_code=404, detail="Borrador inexistente")
    try:
        corrected = apply_tablet_response(rows, response)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    draft_rows[response.note_id] = corrected
    memory.append(response.note_id, "intento", response.model_dump())
    return corrected


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


@app.post("/api/ordenes/{order_id}/cierre", response_model=ClosureComparison)
def register_closure(order_id: str, closure: ClosureReport) -> ClosureComparison:
    order = service.orders.get(order_id)
    if order is None or str(order.id) != str(closure.order_id):
        raise HTTPException(status_code=404, detail="Orden inexistente")
    if order.status != OrderStatus.EXECUTED:
        raise HTTPException(status_code=409, detail="La orden no está Ejecutada")
    comparison = compare_closure(order, closure)
    closures[order_id] = closure
    memory.append(order_id, "cierre", closure.model_dump(mode="json"))
    return comparison


@app.post("/api/ordenes/{order_id}/certificar")
def certify_order(
    order_id: str, contract_prices: dict[str, float]
) -> dict[str, object]:
    order = service.orders.get(order_id)
    closure = closures.get(order_id)
    if order is None or closure is None:
        raise HTTPException(status_code=404, detail="Orden o cierre inexistente")
    if not closure.contractor:
        raise HTTPException(status_code=409, detail="La orden no es de contratista")
    comparison = compare_closure(order, closure)
    if not comparison.matches:
        raise HTTPException(status_code=409, detail=comparison.differences)
    if order.status != OrderStatus.EXECUTED:
        raise HTTPException(status_code=409, detail="La orden no está Ejecutada")
    service.transition_order(order_id, OrderStatus.CERTIFIED)
    habilita = issue_habilita(order, contract_prices)
    return {"order": order, "habilita": habilita}


@app.get("/api/memoria/{note_id}")
def get_memory(note_id: str) -> list[dict[str, Any]]:
    return memory.get(note_id)


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
