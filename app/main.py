from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Query, status

from .contract_messages import (
    alert_message,
    event_message,
    order_message,
    sensor_reading_from_contract,
    state_message,
    tablet_message,
)
from .contract_adapter import load_contract
from .domain import DomainService
from .certification import compare_closure, issue_habilita
from .integrations import (
    VoicePartExtractor,
    WhisperTranscriber,
    apply_tablet_response,
    download_media,
)
from .memory import ConversationMemory
from .mcp import EquipmentMCPServer
from .mqtt_bridge import MqttBridge
from .official_data import equipment_from_definition
from .persistence import build_repository
from .models import (
    ClosureReport,
    ClosureComparison,
    Equipment,
    Event,
    EventStatus,
    FilaParte,
    InventoryQuery,
    ManualSearchQuery,
    MaterialListQuery,
    Order,
    OrderCreate,
    OrderHistoryQuery,
    OrderStatus,
    Part,
    PartCreate,
    SafetyAlert,
    SensorReading,
    TaskCatalogQuery,
    TabletResponse,
    VoiceNote,
)
from .tools import EquipmentQuery, ReadOnlyTools, SensorHistoryQuery

logger = logging.getLogger("planta")
database_url = os.path.expandvars(os.getenv("DATABASE_URL", ""))
repository = build_repository(database_url)
service = DomainService(repository=repository)
tools = ReadOnlyTools(service)
mcp_server = EquipmentMCPServer(tools)
memory = ConversationMemory()
draft_rows: dict[str, list[FilaParte]] = {}
draft_notes: dict[str, VoiceNote] = {}
tablet_notes: dict[str, str] = {}
mqtt_bridge: MqttBridge | None = None


def _publish_event(event: Event, *, nota_ids: list[str] | None = None) -> None:
    if mqtt_bridge is None:
        return
    try:
        mqtt_bridge.publish_event(event_message(event, nota_ids=nota_ids))
    except Exception:
        logger.exception("No se pudo publicar el evento %s", event.id)


def _publish_alert(
    alert: SafetyAlert,
    *,
    equipo: str | None = None,
    parte_id: str | None = None,
    nota_ids: list[str] | None = None,
) -> None:
    if mqtt_bridge is None:
        return
    try:
        mqtt_bridge.publish_event(
            alert_message(alert, equipo=equipo, parte_id=parte_id, nota_ids=nota_ids)
        )
    except Exception:
        logger.exception("No se pudo publicar la alerta %s", alert.id)


def _publish_order(order: Order) -> None:
    if mqtt_bridge is None:
        return
    try:
        mqtt_bridge.publish_order(order_message(order))
    except Exception:
        logger.exception("No se pudo publicar la orden %s", order.id)


def _publish_heartbeat() -> None:
    if mqtt_bridge is None:
        return
    mqtt_bridge.publish_heartbeat(
        os.getenv("SISTEMA_NOMBRE", "planta"),
        mqtt_bridge.enlace_ok,
        len(service.sync_queue),
    )


def _on_sensor(payload: dict[str, Any]) -> None:
    try:
        reading = sensor_reading_from_contract(payload)
        if reading is None:
            return
        event = service.evaluate_sensor(reading)
        if event.status == EventStatus.ESCALATED:
            _publish_event(event)
    except Exception as exc:
        logger.warning("Lectura MQTT rechazada: %s", exc)


def _on_recorrida(payload: dict[str, Any]) -> None:
    try:
        note_contract = load_contract().NotaRecorrida.model_validate(payload)
        transcript = payload.get("transcript")
        if not transcript:
            transcriber = WhisperTranscriber(
                os.getenv("WHISPER_MODEL_PATH", ""),
                device=os.getenv("WHISPER_DEVICE", "cpu"),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
            )
            if not note_contract.audio_url:
                raise ValueError("La nota no trae audio_url ni transcript")
            audio = download_media(
                os.getenv("PLANTA_URL", "http://sim:8100"),
                note_contract.audio_url,
            )
            transcript = transcriber.transcribe(audio)
        note = VoiceNote(
            note_id=note_contract.id,
            observed_at=note_contract.ts,
            operator_id=note_contract.operador,
            recorrido_id=note_contract.recorrida_id,
            audio_url=note_contract.audio_url,
            photo_urls=note_contract.fotos,
            transcript=transcript,
        )
        rows = VoicePartExtractor(list(service.equipment.values())).extract(note, transcript)
        draft_rows[note.note_id] = rows
        draft_notes[note.note_id] = note
        memory.append(note.note_id, "nota", note.model_dump(mode="json"))
        memory.append(note.note_id, "borrador", {"filas": [row.model_dump() for row in rows]})
        _publish_draft(note, rows)
    except Exception as exc:
        logger.exception("No se pudo procesar la recorrida %s: %s", payload.get("id"), exc)
        if payload.get("id"):
            _publish_tablet_error(str(payload["id"]), "No pude interpretar la nota; revise el audio.")


def _on_cierre(payload: dict[str, Any]) -> None:
    logger.info("Nota de cierre recibida: %s", payload.get("id"))


def _on_respuesta(payload: dict[str, Any]) -> None:
    try:
        response = load_contract().RespuestaOperador.model_validate(payload)
        note_id = tablet_notes.get(response.mensaje_id)
        if note_id is None:
            raise ValueError(f"Mensaje de tablet inexistente: {response.mensaje_id}")
        note = draft_notes[note_id]
        if response.texto.strip().casefold().startswith(("no", "nop")):
            rows = VoicePartExtractor(list(service.equipment.values())).extract(
                note, response.texto
            )
        else:
            rows = draft_rows[note_id]
        draft_rows[note_id] = rows
        _confirm_voice_draft(note, rows)
    except Exception as exc:
        logger.exception("No se pudo procesar la respuesta de tablet: %s", exc)


def _publish_draft(note: VoiceNote, rows: list[FilaParte]) -> None:
    if mqtt_bridge is None:
        return
    message_id = f"tablet:{note.note_id}:{uuid4()}"
    tablet_notes[message_id] = note.note_id
    mqtt_bridge.publish_tablet(
        tablet_message(
            message_id=message_id,
            note_ids=[note.note_id],
            texto="Revisá el parte y confirmá o corregí los valores.",
            filas=rows,
            titulo="Borrador de recorrida",
        )
    )


def _publish_tablet_error(note_id: str, text: str) -> None:
    if mqtt_bridge is None:
        return
    mqtt_bridge.publish_tablet(
        tablet_message(
            message_id=f"tablet:error:{note_id}",
            note_ids=[note_id],
            texto=text,
            filas=[],
            espera_respuesta=False,
        )
    )


def _confirm_voice_draft(note: VoiceNote, rows: list[FilaParte]) -> None:
    part = service.save_part(
        Part(
            idempotency_key=f"voice:{note.note_id}",
            operator_id=note.operator_id,
            observed_at=note.observed_at,
            readings=[
                {
                    "equipment_tag": row.equipment_tag,
                    "variable": row.variable,
                    "value": row.value,
                    "unit": row.unit,
                    "observation": row.observation,
                    "photo_ids": row.photo_ids,
                }
                for row in rows
            ],
        )
    )
    results = service.evaluate_part(service.confirm_part(part.idempotency_key))
    for item in results:
        if isinstance(item, SafetyAlert):
            _publish_alert(item, parte_id=str(part.id), nota_ids=[note.note_id])
        else:
            _publish_event(item, nota_ids=[note.note_id])


def _bootstrap_equipment() -> None:
    url = os.getenv("PLANTA_URL", "").strip()
    if not url:
        return
    endpoint = f"{url.rstrip('/')}/api/planta"
    for attempt in range(5):
        try:
            response = httpx.get(endpoint, timeout=3)
            response.raise_for_status()
            for equipment in equipment_from_definition(response.json()):
                if equipment.tag not in service.equipment:
                    service.add_equipment(equipment)
            return
        except Exception as exc:
            if attempt == 4:
                logger.warning("No se pudo cargar la planta desde %s: %s", endpoint, exc)
                return
            time.sleep(2)


def _start_mqtt() -> MqttBridge | None:
    host = os.getenv("MQTT_HOST", "").strip()
    if not host:
        return None
    try:
        bridge = MqttBridge(
            on_recorrida=_on_recorrida,
            on_sensor=_on_sensor,
            on_cierre=_on_cierre,
            on_respuesta=_on_respuesta,
        )
        bridge.start(host, int(os.getenv("MQTT_PORT", "1883")))
        return bridge
    except Exception:
        logger.exception("No se pudo iniciar la conexión MQTT")
        return None


async def _heartbeat_loop() -> None:
    while True:
        _publish_heartbeat()
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global mqtt_bridge
    _bootstrap_equipment()
    mqtt_bridge = _start_mqtt()
    heartbeat = asyncio.create_task(_heartbeat_loop())
    try:
        yield
    finally:
        heartbeat.cancel()
        if mqtt_bridge is not None:
            mqtt_bridge.stop()
            mqtt_bridge = None


app = FastAPI(
    title="Planta de inyección de agua",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, Any]:
    try:
        return state_message(
            os.getenv("SISTEMA_NOMBRE", "planta"),
            mqtt_bridge.enlace_ok if mqtt_bridge is not None else False,
            len(service.sync_queue),
        )
    except Exception:
        return {
            "ts": datetime.now(UTC).isoformat(),
            "sistema": os.getenv("SISTEMA_NOMBRE", "planta"),
            "enlace_ok": mqtt_bridge.enlace_ok if mqtt_bridge is not None else False,
            "pendientes_sincronizar": len(service.sync_queue),
        }


@app.post("/api/equipos", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(equipment: Equipment) -> Equipment:
    return service.add_equipment(equipment)


@app.get("/api/equipos", response_model=list[Equipment])
def list_equipment(tag: str | None = Query(default=None, min_length=1)) -> list[Equipment]:
    return tools.equipment(EquipmentQuery(tag=tag))


@app.get("/api/planta")
def plant_definition() -> dict[str, Any]:
    return {
        "equipos": [
            equipment.model_dump(mode="json")
            for equipment in service.equipment.values()
        ],
        "sensores": [
            {
                "tag": equipment.tag,
                "variable": "presion_descarga",
                "alarma_baja": equipment.alarm_min,
                "alarma_alta": equipment.alarm_max,
            }
            for equipment in service.equipment.values()
            if equipment.alarm_min is not None or equipment.alarm_max is not None
        ],
    }


@app.get("/api/historian/{tag}/{variable}")
def historian(
    tag: str,
    variable: str,
    limit: int = Query(default=1000, ge=1, le=64800),
) -> list[dict[str, Any]]:
    return tools.sensor_history(
        SensorHistoryQuery(tag=tag, variable=variable, limit=limit)
    )


@app.post("/api/partes", response_model=Part, status_code=status.HTTP_201_CREATED)
def create_part(request: PartCreate) -> Part:
    try:
        return service.save_part(Part(**request.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    draft_notes[note.note_id] = note
    memory.append(note.note_id, "nota", note.model_dump(mode="json"))
    memory.append(note.note_id, "borrador", {"filas": [row.model_dump() for row in rows]})
    _publish_draft(note, rows)
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
    if response.accepted:
        note = draft_notes.get(response.note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Nota de recorrida inexistente")
        try:
            if response.corrections and response.corrections.strip().casefold().startswith(
                ("no", "nop")
            ):
                corrected = VoicePartExtractor(list(service.equipment.values())).extract(
                    note, response.corrections
                )
                draft_rows[response.note_id] = corrected
            _confirm_voice_draft(note, corrected)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    return corrected


@app.post("/api/partes/{idempotency_key}/confirmar", response_model=list[Event | SafetyAlert])
def confirm_part(idempotency_key: str) -> list[Event | SafetyAlert]:
    try:
        part = service.confirm_part(idempotency_key)
        results = service.evaluate_part(part)
        equipo = part.readings[0].equipment_tag if part.readings else None
        for item in results:
            if isinstance(item, SafetyAlert):
                _publish_alert(item, equipo=equipo, parte_id=str(part.id))
            else:
                _publish_event(item)
        return results
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Parte inexistente") from exc


@app.post("/api/sensores", response_model=Event)
def ingest_sensor(reading: SensorReading) -> Event:
    try:
        event = service.evaluate_sensor(reading)
        _publish_event(event)
        return event
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/eventos", response_model=list[Event])
def list_events() -> list[Event]:
    return list(service.events.values())


@app.get("/api/alertas-seguridad", response_model=list[SafetyAlert])
def list_alerts() -> list[SafetyAlert]:
    return list(service.alerts.values())


@app.post("/api/ordenes", response_model=Order)
def create_order(request: OrderCreate) -> Order:
    event = service.get_event(request.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento inexistente")
    if event.status != EventStatus.ESCALATED:
        raise HTTPException(status_code=409, detail="Solo un evento Escalado puede generar una orden")
    if event.equipment_tag != request.equipment_tag:
        raise HTTPException(status_code=422, detail="La orden no coincide con el equipo del evento")
    order = service.create_order(Order(**request.model_dump()))
    _publish_order(order)
    return order


@app.post("/api/ordenes/{order_id}/transicion", response_model=Order)
def transition_order(order_id: str, target: OrderStatus, reason: str | None = None) -> Order:
    try:
        order = service.transition_order(order_id, target, reason)
        _publish_order(order)
        return order
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
    service.attach_closure(order_id, closure)
    memory.append(order_id, "cierre", closure.model_dump(mode="json"))
    return comparison


@app.post("/api/ordenes/{order_id}/certificar")
def certify_order(
    order_id: str
) -> dict[str, object]:
    order = service.orders.get(order_id)
    if order is None or order.closure is None:
        raise HTTPException(status_code=404, detail="Orden o cierre inexistente")
    closure = order.closure
    if order.internal_staff or not closure.contractor:
        raise HTTPException(status_code=409, detail="La orden no es de contratista")
    comparison = compare_closure(order, closure)
    if not comparison.matches:
        raise HTTPException(status_code=409, detail=comparison.differences)
    if order.status != OrderStatus.EXECUTED:
        raise HTTPException(status_code=409, detail="La orden no está Ejecutada")

    prices_raw = os.getenv("CONTRACT_PRICES_JSON")
    if not prices_raw:
        raise HTTPException(status_code=503, detail="Precios contractuales no configurados")
    try:
        prices_data = json.loads(prices_raw)
        if not isinstance(prices_data, dict):
            raise ValueError("El contrato de precios debe ser un objeto")
        contract_prices = {key: float(value) for key, value in prices_data.items()}
        if any(price < 0 for price in contract_prices.values()):
            raise ValueError("Los precios contractuales no pueden ser negativos")
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Precios contractuales inválidos") from exc

    try:
        habilita = issue_habilita(order, contract_prices)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    previous_status = order.status
    order.habilita = habilita
    try:
        service.transition_order(order_id, OrderStatus.CERTIFIED)
    except Exception:
        order.habilita = None
        order.status = previous_status
        raise
    _publish_order(order)
    return {"order": order, "habilita": habilita}


@app.get("/api/memoria/{note_id}")
def get_memory(note_id: str) -> list[dict[str, Any]]:
    return memory.get(note_id)


@app.get("/api/ordenes", response_model=list[Order])
def list_orders() -> list[Order]:
    return list(service.orders.values())


@app.get("/api/tools/equipos", response_model=list[Equipment])
def tool_equipment(tag: str | None = Query(default=None, min_length=1)) -> list[Equipment]:
    return tools.equipment(EquipmentQuery(tag=tag))


@app.get("/api/tools/sensores")
def tool_sensor_history(
    tag: str = Query(min_length=1),
    variable: str = Query(min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    return tools.sensor_history(SensorHistoryQuery(tag=tag, variable=variable, limit=limit))


@app.get("/api/tools/ordenes")
def tool_order_history(
    equipment_tag: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    return tools.order_history(OrderHistoryQuery(equipment_tag=equipment_tag, limit=limit))


@app.get("/api/tools/inventario")
def tool_inventory(
    equipment_tag: str | None = Query(default=None, min_length=1),
    code: str | None = Query(default=None, min_length=1),
) -> list[dict[str, Any]]:
    return tools.inventory(InventoryQuery(equipment_tag=equipment_tag, code=code))


@app.get("/api/tools/materiales")
def tool_materials(equipment_tag: str = Query(min_length=1)) -> list[dict[str, Any]]:
    return tools.materials(MaterialListQuery(equipment_tag=equipment_tag))


@app.get("/api/tools/tareas")
def tool_tasks(
    equipment_tag: str | None = Query(default=None, min_length=1),
) -> list[dict[str, Any]]:
    return tools.tasks(TaskCatalogQuery(equipment_tag=equipment_tag))


@app.get("/api/tools/manuales")
def tool_manuals(
    question: str = Query(min_length=1, max_length=500),
    equipment_tag: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[dict[str, Any]]:
    return tools.manuals(
        ManualSearchQuery(question=question, equipment_tag=equipment_tag, limit=limit)
    )


@app.get("/api/mcp/tools")
def mcp_tools() -> list[str]:
    return mcp_server.list_tools()


@app.post("/api/mcp/call")
def mcp_call(name: str, arguments: dict[str, Any]) -> list[Any]:
    try:
        return mcp_server.call(name, arguments)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
