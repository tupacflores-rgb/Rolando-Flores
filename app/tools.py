from __future__ import annotations

from typing import Any

from pydantic import Field

from .models import (
    Equipment,
    InventoryQuery,
    ManualSearchQuery,
    MaterialListQuery,
    OrderHistoryQuery,
    RetrievalQuery,
    StrictModel,
    TaskCatalogQuery,
)


class EquipmentQuery(StrictModel):
    tag: str | None = Field(default=None, min_length=1)


class SensorHistoryQuery(StrictModel):
    tag: str = Field(min_length=1)
    variable: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=64800)


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

    def order_history(self, query: OrderHistoryQuery) -> list[dict[str, Any]]:
        orders = [
            order.model_dump(mode="json")
            for order in self.service.orders.values()
            if query.equipment_tag is None or order.equipment_tag == query.equipment_tag
        ]
        return orders[-query.limit :]

    def inventory(self, query: InventoryQuery) -> list[dict[str, Any]]:
        catalog = getattr(self.service, "inventory_catalog", [])
        return [
            item for item in catalog
            if (query.code is None or item.get("codigo") == query.code)
            and (
                query.equipment_tag is None
                or query.equipment_tag in item.get("equipos", [])
            )
        ]

    def materials(self, query: MaterialListQuery) -> list[dict[str, Any]]:
        return [
            item for item in getattr(self.service, "material_catalog", {}).get(
                query.equipment_tag, []
            )
        ]

    def tasks(self, query: TaskCatalogQuery) -> list[dict[str, Any]]:
        tasks = getattr(self.service, "task_catalog", [])
        return [
            item for item in tasks
            if query.equipment_tag is None
            or query.equipment_tag in item.get("equipos", [])
        ]

    def manuals(self, query: ManualSearchQuery) -> list[dict[str, Any]]:
        index = getattr(self.service, "manual_index", None)
        if index is None:
            return []
        results = index.search(
            RetrievalQuery(
                question=query.question,
                equipment_tag=query.equipment_tag,
                k=query.limit,
            )
        )
        return [
            {
                "citation": result.chunk.citation,
                "text": result.chunk.text,
                "score": result.score,
            }
            for result in results[: query.limit]
        ]
