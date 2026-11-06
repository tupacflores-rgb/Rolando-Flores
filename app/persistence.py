from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from .models import Equipment, Event, Order, Part, SafetyAlert, SensorReading


class PostgresRepository:
    """Persistencia transaccional del dominio; el contrato de negocio sigue en DomainService."""

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg es obligatorio para la persistencia PostgreSQL") from exc
        self.connection = psycopg.connect(dsn, autocommit=True)

    def save_equipment(self, equipment: Equipment) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO equipment
                    (tag, name, aliases, kind, alarm_min, alarm_max, normal_state, reserve_available, sensor_limits)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (tag) DO UPDATE SET
                    name=EXCLUDED.name, aliases=EXCLUDED.aliases, kind=EXCLUDED.kind,
                    alarm_min=EXCLUDED.alarm_min, alarm_max=EXCLUDED.alarm_max,
                    normal_state=EXCLUDED.normal_state,
                    reserve_available=EXCLUDED.reserve_available,
                    sensor_limits=EXCLUDED.sensor_limits
                """,
                (
                    equipment.tag,
                    equipment.name,
                    json.dumps(equipment.aliases),
                    equipment.kind,
                    equipment.alarm_min,
                    equipment.alarm_max,
                    equipment.normal_state,
                    equipment.reserve_available,
                    json.dumps({
                        key: value.model_dump()
                        for key, value in equipment.sensor_limits.items()
                    }),
                ),
            )

    def save_part(self, part: Part) -> None:
        self._save_payload(
            "parts",
            "id, idempotency_key, status, observed_at, payload",
            (str(part.id), part.idempotency_key, part.status.value, part.observed_at, json.dumps(part.model_dump(mode="json"))),
            "idempotency_key",
        )

    def save_sensor(self, reading: SensorReading) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sensor_readings
                    (id, idempotency_key, equipment_tag, variable, value, unit, observed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (str(uuid4()), reading.idempotency_key, reading.equipment_tag,
                 reading.variable, reading.value, reading.unit, reading.observed_at),
            )

    def save_event(self, event: Event) -> None:
        self._save_payload(
            "events",
            "id, idempotency_key, origin, source_id, status, equipment_tag, variable, value, context, created_at",
            (str(event.id), event.idempotency_key, event.origin, event.source_id, event.status.value,
             event.equipment_tag, event.variable, event.value, json.dumps(event.context), event.created_at),
            "idempotency_key",
        )

    def save_alert(self, alert: SafetyAlert) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO safety_alerts (id, code, source_id, message, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO NOTHING
                """,
                (str(alert.id), alert.code, alert.source_id, alert.message, alert.created_at),
            )

    def save_order(self, order: Order) -> None:
        self._save_payload(
            "work_orders",
            "id, event_id, equipment_tag, status, payload, created_at",
            (str(order.id), str(order.event_id), order.equipment_tag, order.status.value,
             json.dumps(order.model_dump(mode="json")), order.created_at),
            "event_id",
        )

    def save_sync(self, item: dict[str, Any]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sync_queue
                    (id, idempotency_key, operation, payload, attempts, synced, last_error)
                VALUES (gen_random_uuid(), %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO UPDATE SET
                    operation=EXCLUDED.operation, payload=EXCLUDED.payload,
                    attempts=EXCLUDED.attempts, synced=EXCLUDED.synced,
                    last_error=EXCLUDED.last_error
                """,
                (item["idempotency_key"], item["operation"], json.dumps(item["payload"]),
                 item["attempts"], item["synced"], item.get("last_error")),
            )

    def save_memory(self, note_id: str, kind: str, payload: dict[str, Any], created_at: Any) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversation_memory (id, note_id, kind, payload, created_at)
                VALUES (gen_random_uuid(), %s, %s, %s::jsonb, %s)
                """,
                (note_id, kind, json.dumps(payload), created_at),
            )

    def restore_memory(self) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT note_id, kind, payload, created_at FROM conversation_memory ORDER BY created_at"
            )
            return [
                {
                    "note_id": row[0],
                    "kind": row[1],
                    "payload": row[2],
                    "created_at": row[3],
                }
                for row in cursor.fetchall()
            ]

    def restore(self) -> dict[str, list[Any]]:
        restored: dict[str, list[Any]] = {
            "equipment": [], "parts": [], "sensor_readings": [],
            "events": [], "alerts": [], "orders": [], "sync": []
        }
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT tag, name, aliases, kind, alarm_min, alarm_max, normal_state, reserve_available "
                ", sensor_limits FROM equipment"
            )
            for row in cursor.fetchall():
                restored["equipment"].append(
                    Equipment(
                        tag=row[0], name=row[1], aliases=row[2], kind=row[3],
                        alarm_min=row[4], alarm_max=row[5], normal_state=row[6],
                        reserve_available=row[7], sensor_limits=row[8],
                    )
                )
            cursor.execute(
                "SELECT idempotency_key, equipment_tag, variable, value, unit, observed_at "
                "FROM sensor_readings ORDER BY observed_at"
            )
            restored["sensor_readings"] = [
                SensorReading(
                    idempotency_key=row[0], equipment_tag=row[1], variable=row[2],
                    value=row[3], unit=row[4], observed_at=row[5],
                )
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT payload FROM parts")
            restored["parts"] = [Part.model_validate(row[0]) for row in cursor.fetchall()]
            cursor.execute("SELECT payload FROM work_orders")
            restored["orders"] = [Order.model_validate(row[0]) for row in cursor.fetchall()]
            cursor.execute(
                "SELECT id, idempotency_key, origin, source_id, status, equipment_tag, "
                "variable, value, context, created_at FROM events"
            )
            restored["events"] = [
                Event(
                    id=row[0], idempotency_key=row[1], origin=row[2], source_id=row[3],
                    status=row[4], equipment_tag=row[5], variable=row[6], value=row[7],
                    context=row[8], created_at=row[9],
                )
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT id, code, source_id, message, created_at FROM safety_alerts")
            restored["alerts"] = [
                SafetyAlert(
                    id=row[0], code=row[1], source_id=row[2], message=row[3],
                    created_at=row[4],
                )
                for row in cursor.fetchall()
            ]
            cursor.execute(
                "SELECT idempotency_key, operation, payload, attempts, synced, last_error "
                "FROM sync_queue WHERE synced = FALSE ORDER BY id"
            )
            restored["sync"] = [
                {
                    "idempotency_key": row[0],
                    "operation": row[1],
                    "payload": row[2],
                    "attempts": row[3],
                    "synced": row[4],
                    "last_error": row[5],
                }
                for row in cursor.fetchall()
            ]
        return restored

    def _save_payload(
        self, table: str, columns: str, values: tuple[Any, ...], conflict_column: str
    ) -> None:
        placeholders = ", ".join(["%s"] * len(values))
        updates = {
            "parts": "status=EXCLUDED.status, observed_at=EXCLUDED.observed_at, payload=EXCLUDED.payload",
            "events": "status=EXCLUDED.status, context=EXCLUDED.context",
            "work_orders": "status=EXCLUDED.status, payload=EXCLUDED.payload",
        }
        update = updates.get(table, "payload=EXCLUDED.payload")
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) "
                f"ON CONFLICT ({conflict_column}) DO UPDATE SET {update}",
                values,
            )


def build_repository(database_url: str | None) -> PostgresRepository | None:
    if not database_url:
        return None
    return PostgresRepository(database_url)
