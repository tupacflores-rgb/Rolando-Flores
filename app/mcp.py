from __future__ import annotations

from .tools import EquipmentQuery, ReadOnlyTools


class EquipmentMCPServer:
    """Superficie MCP mínima; el transporte se conecta en el despliegue."""

    name = "planta-equipment"

    def __init__(self, tools: ReadOnlyTools) -> None:
        self.tools = tools

    def list_tools(self) -> list[str]:
        return ["equipos"]

    def call(self, name: str, arguments: dict) -> list:
        if name != "equipos":
            raise ValueError(f"Tool MCP inexistente: {name}")
        return self.tools.equipment(EquipmentQuery.model_validate(arguments))
