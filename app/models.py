from __future__ import annotations

from datetime import UTC, datetime
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


class OrderHistoryQuery(StrictModel):
    equipment_tag: str | None = Field(default=None, min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)


class InventoryQuery(StrictModel):
    equipment_tag: str | None = Field(default=None, min_length=1)
    code: str | None = Field(default=None, min_length=1)


class MaterialListQuery(StrictModel):
    equipment_tag: str = Field(min_length=1)


class TaskCatalogQuery(StrictModel):
    equipment_tag: str | None = Field(default=None, min_length=1)


class ManualSearchQuery(StrictModel):
    question: str = Field(min_length=1, max_length=500)
    equipment_tag: str | None = Field(default=None, min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SafetyAlert(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    code: str = Field(pattern=r"^S[1-4]$")
    message: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
    detiene_equipo: bool = False
    reduce_inyeccion: bool = False


class ClosureReport(StrictModel):
    order_id: UUID
    technician: str = Field(min_length=1)
    contractor: bool = False
    tasks_done: list[str] = Field(min_length=1)
    parts_used: list[str] = Field(default_factory=list)
    hours: float = Field(ge=0)
    final_test: str = Field(min_length=1)
    photo_ids: list[str] = Field(default_factory=list)


class ClosureComparison(StrictModel):
    order_id: UUID
    missing_tasks: list[str] = Field(default_factory=list)
    unexpected_tasks: list[str] = Field(default_factory=list)
    missing_parts: list[str] = Field(default_factory=list)
    unexpected_parts: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    matches: bool


class Habilita(StrictModel):
    number: str
    order_id: UUID
    amount_usd: float = Field(ge=0)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Order(OrderCreate):
    id: UUID = Field(default_factory=uuid4)
    status: OrderStatus = OrderStatus.DRAFT
    approval_reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    closure: ClosureReport | None = None
    habilita: Habilita | None = None


class SyncItem(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    idempotency_key: str
    operation: str
    payload: dict[str, Any]
    attempts: int = 0
    synced: bool = False
    last_error: str | None = None


class FilaParte(StrictModel):
    equipment_tag: str = Field(min_length=1)
    variable: str = Field(min_length=1)
    value: float | None = None
    unit: str | None = None
    observed_at: datetime
    observation: str | None = None
    photo_ids: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_reason: str | None = None


class VoiceNote(StrictModel):
    note_id: str = Field(min_length=1)
    observed_at: datetime
    operator_id: str = Field(default="operador", min_length=1, max_length=80)
    recorrido_id: str | None = None
    audio_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    transcript: str | None = None


class TabletResponse(StrictModel):
    note_id: str = Field(min_length=1)
    accepted: bool
    corrections: str | None = None


class ToolAudit(StrictModel):
    tool_name: str
    arguments: dict[str, Any]
    duration_ms: int = Field(ge=0)
    tokens: int = Field(default=0, ge=0)
    error: str | None = None


class ManualChunk(StrictModel):
    equipment_tag: str
    manufacturer: str
    document: str
    section: str
    citation: str
    text: str
    vigente: bool = True
    embedding: list[float] | None = None


class RetrievalQuery(StrictModel):
    question: str = Field(min_length=1)
    equipment_tag: str | None = None
    k: int = Field(default=5, ge=1, le=20)


class ProbableCause(StrictModel):
    cause: str
    evidence: list[str] = Field(default_factory=list)
    missing_confirmation: list[str] = Field(default_factory=list)
    citation: str


class WorkOrderEvidence(StrictModel):
    event_id: UUID
    photo_ids: list[str] = Field(default_factory=list)
    sensor_trend: list[dict[str, Any]] = Field(default_factory=list)
    causes: list[ProbableCause] = Field(default_factory=list)
