from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PartStatus(StrEnum):
    DRAFT = "Borrador"
    CONFIRMED = "Confirmado"


class EventStatus(StrEnum):
    NORMAL = "Sin novedad"
    ESCALATED = "Escalado"
    SAFETY = "Alerta de seguridad"


class OrderStatus(StrEnum):
    DRAFT = "Borrador"
    PENDING = "Pendiente de aprobación"
    APPROVED = "Aprobada"
    REJECTED = "Rechazada"
    EXECUTED = "Ejecutada"
    OBSERVED = "Observada"
    CLOSED = "Cerrada"
    CERTIFIED = "Certificada"


class Equipment(StrictModel):
    tag: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    aliases: list[str] = Field(default_factory=list)
    kind: str = Field(min_length=1, max_length=40)
    operating_min: float | None = None
    operating_max: float | None = None
    alarm_min: float | None = None
    alarm_max: float | None = None
    normal_state: str | None = None
    reserve_available: bool = False


class PartReading(StrictModel):
    equipment_tag: str = Field(min_length=1)
    variable: str = Field(min_length=1)
    value: float | None = None
    unit: str | None = None
    observation: str | None = None
    photo_ids: list[str] = Field(default_factory=list)


class PartCreate(StrictModel):
    idempotency_key: str = Field(min_length=1, max_length=128)
    operator_id: str = Field(min_length=1, max_length=80)
    observed_at: datetime
    readings: list[PartReading] = Field(min_length=1)


class Part(PartCreate):
    id: UUID = Field(default_factory=uuid4)
    status: PartStatus = PartStatus.DRAFT


class SensorReading(StrictModel):
    idempotency_key: str = Field(min_length=1, max_length=128)
    equipment_tag: str = Field(min_length=1)
    variable: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    observed_at: datetime


class Event(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    idempotency_key: str = Field(min_length=1)
    origin: str = Field(pattern=r"^(part|sensor)$")
    source_id: str = Field(min_length=1)
    status: EventStatus
    equipment_tag: str
    variable: str | None = None
    value: float | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SafetyAlert(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    code: str = Field(pattern=r"^S[1-4]$")
    message: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    emergency_procedure: str = "Avisar por radio al supervisor de turno"
    wait_for_response: bool = False


class OrderCreate(StrictModel):
    event_id: UUID
    equipment_tag: str
    task: str = Field(min_length=1)
    parts: list[str] = Field(default_factory=list)
    total_cost_usd: float = Field(ge=0)
    stock_available: bool
    standard_task: bool
    keeps_injection: bool
    internal_staff: bool
    structural_damage: bool = False


class Order(OrderCreate):
    id: UUID = Field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.DRAFT
    approval_reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SyncItem(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    idempotency_key: str
    operation: str
    payload: dict[str, Any]
    attempts: int = 0
    synced: bool = False
    last_error: str | None = None

