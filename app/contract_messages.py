from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .contract_adapter import load_contract
from .models import (
    Event,
    EventStatus,
    FilaParte,
    Order,
    OrderStatus,
    SafetyAlert,
    SensorReading,
)

_EVENT_TYPES = {
    EventStatus.NORMAL: "SinNovedad",
    EventStatus.ESCALATED: "Escalado",
    EventStatus.SAFETY: "AlertaSeguridad",
}

_ORDER_STATES = {
    OrderStatus.DRAFT: "Borrador",
    OrderStatus.PENDING: "PendienteAprobacion",
    OrderStatus.APPROVED: "Aprobada",
    OrderStatus.REJECTED: "Rechazada",
    OrderStatus.EXECUTED: "Ejecutada",
    OrderStatus.OBSERVED: "Observada",
    OrderStatus.CLOSED: "Cerrada",
    OrderStatus.CERTIFIED: "Certificada",
}


def state_message(
    sistema: str, enlace_ok: bool, pendientes: int
) -> dict[str, Any]:
    contract = load_contract()
    return contract.EstadoSistema(
        ts=datetime.now(UTC),
        sistema=sistema,
        enlace_ok=enlace_ok,
        pendientes_sincronizar=pendientes,
    ).model_dump(mode="json")


def event_message(
    event: Event, *, nota_ids: list[str] | None = None
) -> dict[str, Any]:
    contract = load_contract()
    return contract.EventoSistema(
        id=str(event.id),
        ts=event.created_at,
        tipo=_EVENT_TYPES[event.status],
        equipo=event.equipment_tag or None,
        origen="parte" if event.origin == "part" else "sensor",
        parte_id=event.source_id if event.origin == "part" else None,
        nota_ids=nota_ids or [],
        resumen=str(event.context.get("reason") or event.status.value),
    ).model_dump(mode="json")


def alert_message(
    alert: SafetyAlert,
    *,
    equipo: str | None = None,
    parte_id: str | None = None,
    nota_ids: list[str] | None = None,
) -> dict[str, Any]:
    contract = load_contract()
    return contract.EventoSistema(
        id=str(alert.id),
        ts=alert.created_at,
        tipo="AlertaSeguridad",
        equipo=equipo,
        origen="parte",
        parte_id=parte_id,
        nota_ids=nota_ids or [],
        resumen=alert.message,
    ).model_dump(mode="json")


def order_message(order: Order) -> dict[str, Any]:
    contract = load_contract()
    return contract.OrdenSistema(
        id=str(order.id),
        ts=datetime.now(UTC),
        estado=_ORDER_STATES[order.status],
        equipo=order.equipment_tag,
        evento_ids=[str(order.event_id)],
        tareas=[order.task],
        detiene_equipo=order.detiene_equipo,
        reduce_inyeccion=order.reduce_inyeccion or not order.keeps_injection,
        ejecutor="propio" if order.internal_staff else "contratista",
        repuestos=[
            contract.Repuesto(codigo=part, cantidad=1.0)
            for part in order.parts
        ],
        motivo="; ".join(order.approval_reasons) or None,
        habilita=order.habilita.number if order.habilita else None,
        monto_habilita_usd=order.habilita.amount_usd if order.habilita else None,
    ).model_dump(mode="json")


def tablet_message(
    *,
    message_id: str,
    note_ids: list[str],
    texto: str,
    filas: list[FilaParte],
    titulo: str | None = None,
    opciones: list[str] | None = None,
    espera_respuesta: bool = True,
) -> dict[str, Any]:
    contract = load_contract()
    return contract.MensajeTablet(
        id=message_id,
        ts=datetime.now(UTC),
        nota_ids=note_ids,
        texto=texto,
        pantalla=contract.Pantalla(
            titulo=titulo,
            filas=[
                contract.FilaParte(
                    tag=row.equipment_tag,
                    variable=row.variable,
                    valor=row.value,
                    unidad=row.unit,
                    observacion=row.observation,
                )
                for row in filas
            ],
            opciones=opciones or [],
        ),
        espera_respuesta=espera_respuesta,
    ).model_dump(mode="json")


def sensor_reading_from_contract(payload: dict[str, Any]) -> SensorReading | None:
    contract = load_contract()
    lectura = contract.LecturaSensor.model_validate(payload)
    if lectura.valor is None or lectura.calidad.value == "sin_dato":
        return None
    key = (
        f"sensor:{lectura.tag}:{lectura.variable}:"
        f"{lectura.ts.isoformat()}:{lectura.valor}"
    )
    return SensorReading(
        idempotency_key=key[:128],
        equipment_tag=lectura.tag,
        variable=lectura.variable,
        value=float(lectura.valor),
        unit=lectura.unidad,
        observed_at=lectura.ts,
    )
