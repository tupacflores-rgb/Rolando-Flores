from __future__ import annotations

from typing import Any

from pydantic import Field

from .models import Equipment, StrictModel


class EquipmentQuery(StrictModel):
    tag: str | None = Field(default=None, min_length=1)


class SensorHistoryQuery(StrictModel):
    tag: str = Field(min_length=1)
    variable: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)


class ReadOnlyTools:
    def __init__(self, service) -> None:
        self.service = service

    def equipment(self, query: EquipmentQuery) -> list[Equipment]:
        if query.tag:
            equipment = self.service.equipment.get(query.tag)
            return [] if equipment is None else [equipment]
        return list(self.service.equipment.values())

    def sensor_history(self, query: SensorHistoryQuery) -> list[dict[str, Any]]:
        return [
            {"equipment_tag": query.tag, "variable": query.variable, "value": value, "observed_at": when}
            for (tag, variable), values in self.service._sustained.items()
            if tag == query.tag and variable == query.variable
            for when, value in values[-query.limit :]
        ]

