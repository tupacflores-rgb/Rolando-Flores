from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class ConversationMemory:
    """Memoria acotada por nota; no retiene audio ni datos fuera de la operación."""

    def __init__(self, retention_days: int = 45) -> None:
        self.retention = timedelta(days=retention_days)
        self._items: dict[str, list[dict[str, Any]]] = {}

    def append(self, note_id: str, kind: str, payload: dict[str, Any]) -> None:
        self._items.setdefault(note_id, []).append(
            {"kind": kind, "payload": payload, "created_at": datetime.utcnow()}
        )

    def get(self, note_id: str, now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.utcnow()
        return [
            item
            for item in self._items.get(note_id, [])
            if current - item["created_at"] <= self.retention
        ]

    def purge(self, now: datetime | None = None) -> int:
        current = now or datetime.utcnow()
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
