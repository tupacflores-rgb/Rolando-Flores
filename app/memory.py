from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


class ConversationMemory:
    """Memoria acotada por nota; no retiene audio ni datos fuera de la operación.

    Si recibe un ``repository``, persiste cada evento de conversación en
    PostgreSQL y restaura el estado al iniciar; si no, opera en RAM (con la
    misma política de retención) y lo documenta explícitamente.
    """

    def __init__(self, retention_days: int = 45, repository=None) -> None:
        self.retention = timedelta(days=retention_days)
        self.repository = repository
        self._items: dict[str, list[dict[str, Any]]] = {}
        if self.repository and hasattr(self.repository, "restore_memory"):
            try:
                for row in self.repository.restore_memory():
                    self._items.setdefault(row["note_id"], []).append(
                        {
                            "kind": row["kind"],
                            "payload": row["payload"],
                            "created_at": row["created_at"],
                        }
                    )
            except Exception:
                # Sin tabla de memoria (despliegue viejo): arranca en RAM.
                pass

    @property
    def persistent(self) -> bool:
        return self.repository is not None and hasattr(self.repository, "save_memory")

    def append(self, note_id: str, kind: str, payload: dict[str, Any]) -> None:
        created_at = datetime.now(UTC)
        self._items.setdefault(note_id, []).append(
            {"kind": kind, "payload": payload, "created_at": created_at}
        )
        if self.persistent:
            try:
                self.repository.save_memory(note_id, kind, payload, created_at)
            except Exception:
                # Si la base no tiene la tabla (despliegue viejo), degrada a RAM.
                pass

    def get(self, note_id: str, now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        return [
            item
            for item in self._items.get(note_id, [])
            if current - item["created_at"] <= self.retention
        ]

    def purge(self, now: datetime | None = None) -> int:
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        removed = 0
        for note_id in list(self._items):
            before = len(self._items[note_id])
            self._items[note_id] = [
                item
                for item in self._items[note_id]
                if current - item["created_at"] <= self.retention
            ]
            removed += before - len(self._items[note_id])
            if not self._items[note_id]:
                del self._items[note_id]
        return removed
