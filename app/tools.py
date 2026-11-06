from __future__ import annotations

import os
from time import perf_counter
from typing import Any

from pydantic import Field

from .historian import HistorianClient
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
    def __init__(self, service, historian: HistorianClient | None = None) -> None:
        self.service = service
        self.historian = historian or HistorianClient(os.getenv("PLANTA_URL", ""))

    def _audit(self, name: str, arguments: dict[str, Any], started: float) -> None:
        self.service.tool_audits.append(
            {
                "tool_name": name,
                "arguments": arguments,
                "duration_ms": max(0, round((perf_counter() - started) * 1000)),
                "tokens": 0,
                "error": None,
            }
        )

    def equipment(self, query: EquipmentQuery) -> list[Equipment]:
        started = perf_counter()
        if query.tag:
            equipment = self.service.equipment.get(query.tag)
            result = [] if equipment is None else [equipment]
        else:
            result = list(self.service.equipment.values())
        self._audit("equipos", query.model_dump(), started)
        return result

    def sensor_history(self, query: SensorHistoryQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        local = sorted(
            (
                reading
                for reading in self.service.sensor_readings.values()
                if reading.equipment_tag == query.tag
                and reading.variable == query.variable
            ),
            key=lambda reading: reading.observed_at,
        )
        merged: dict[tuple, dict[str, Any]] = {}
        for reading in local:
            key = (reading.observed_at.isoformat(), reading.value)
            merged[key] = {
                "equipment_tag": reading.equipment_tag,
                "variable": reading.variable,
                "value": reading.value,
                "observed_at": reading.observed_at,
            }
        for item in self.historian.sensor_history(query.tag, query.variable):
            if not isinstance(item, dict) or "valor" not in item:
                continue
            ts = item.get("ts") or item.get("observed_at")
            value = item.get("valor", item.get("value"))
            key = (str(ts), value)
            if key not in merged:
                merged[key] = {
                    "equipment_tag": query.tag,
                    "variable": query.variable,
                    "value": value,
                    "observed_at": ts,
                }
        result = sorted(merged.values(), key=lambda row: str(row["observed_at"]))
        self._audit("historial_sensores", query.model_dump(), started)
        return result[-query.limit :]

    def order_history(self, query: OrderHistoryQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in self.historian.order_history(query.equipment_tag):
            if not isinstance(item, dict):
                continue
            oid = str(item.get("id") or item.get("numero") or item.get("orden_id") or id(item))
            if oid in seen:
                continue
            seen.add(oid)
            merged.append(item)
        for order in self.service.orders.values():
            if query.equipment_tag is not None and order.equipment_tag != query.equipment_tag:
                continue
            if str(order.id) in seen:
                continue
            seen.add(str(order.id))
            merged.append(order.model_dump(mode="json"))
        self._audit("historial_ordenes", query.model_dump(), started)
        return merged[-query.limit :]

    def inventory(self, query: InventoryQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        catalog = getattr(self.service, "inventory_catalog", [])
        result = [
            item for item in catalog
            if (query.code is None or item.get("codigo") == query.code)
            and (
                query.equipment_tag is None
                or query.equipment_tag in item.get("equipos", [])
            )
        ]
        self._audit("inventario", query.model_dump(), started)
        return result

    def materials(self, query: MaterialListQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        result = [
            item for item in getattr(self.service, "material_catalog", {}).get(
                query.equipment_tag, []
            )
        ]
        self._audit("materiales", query.model_dump(), started)
        return result

    def tasks(self, query: TaskCatalogQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        tasks = getattr(self.service, "task_catalog", [])
        result = [
            item for item in tasks
            if query.equipment_tag is None
            or query.equipment_tag in item.get("equipos", [])
        ]
        self._audit("tareas", query.model_dump(), started)
        return result

    def manuals(self, query: ManualSearchQuery) -> list[dict[str, Any]]:
        started = perf_counter()
        index = getattr(self.service, "manual_index", None)
        if index is None:
            result = []
        else:
            results = index.search(
                RetrievalQuery(
                    question=query.question,
                    equipment_tag=query.equipment_tag,
                    k=query.limit,
                )
            )
            result = [
                {
                    "citation": result.chunk.citation,
                    "text": result.chunk.text,
                    "score": result.score,
                }
                for result in results[: query.limit]
            ]
        self._audit("manuales", query.model_dump(), started)
        return result
