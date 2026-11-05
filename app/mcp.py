from __future__ import annotations

from .models import (
    InventoryQuery,
    ManualSearchQuery,
    MaterialListQuery,
    OrderHistoryQuery,
    TaskCatalogQuery,
)
from .tools import EquipmentQuery, ReadOnlyTools, SensorHistoryQuery


class EquipmentMCPServer:
    """Superficie MCP mínima; el transporte se conecta en el despliegue."""

    name = "planta-equipment"

    def __init__(self, tools: ReadOnlyTools) -> None:
        self.tools = tools

    def list_tools(self) -> list[str]:
        return [
            "equipos",
            "historial_sensores",
            "historial_ordenes",
            "inventario",
            "materiales",
            "tareas",
            "manuales",
        ]

    def call(self, name: str, arguments: dict) -> list:
        if name != "equipos":
            queries = {
                "historial_sensores": (SensorHistoryQuery, self.tools.sensor_history),
                "historial_ordenes": (OrderHistoryQuery, self.tools.order_history),
                "inventario": (InventoryQuery, self.tools.inventory),
                "materiales": (MaterialListQuery, self.tools.materials),
                "tareas": (TaskCatalogQuery, self.tools.tasks),
                "manuales": (ManualSearchQuery, self.tools.manuals),
            }
            if name not in queries:
                raise ValueError(f"Tool MCP inexistente: {name}")
            model, handler = queries[name]
            return handler(model.model_validate(arguments))
        return self.tools.equipment(EquipmentQuery.model_validate(arguments))
