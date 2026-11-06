from __future__ import annotations

import json
import sys
from typing import Any

from .models import (
    InventoryQuery,
    ManualSearchQuery,
    MaterialListQuery,
    OrderHistoryQuery,
    TaskCatalogQuery,
)
from .tools import EquipmentQuery, ReadOnlyTools, SensorHistoryQuery

MCP_PROTOCOL_VERSION = "2024-11-05"

# Esquemas JSON de entrada de cada tool expuesta por MCP.
_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "equipos": {
        "description": "Lista los equipos de la planta, opcionalmente filtrados por tag.",
        "inputSchema": {
            "type": "object",
            "properties": {"tag": {"type": "string"}},
        },
    },
    "historial_sensores": {
        "description": "Historial de un sensor (tag y variable), con caché si el enlace cae.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string"},
                "variable": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["tag", "variable"],
        },
    },
    "historial_ordenes": {
        "description": "Historial de órdenes de trabajo, opcionalmente por equipo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "equipment_tag": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    "inventario": {
        "description": "Inventario y stock, opcionalmente por equipo o código.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "equipment_tag": {"type": "string"},
                "code": {"type": "string"},
            },
        },
    },
    "materiales": {
        "description": "Lista de materiales de un equipo.",
        "inputSchema": {
            "type": "object",
            "properties": {"equipment_tag": {"type": "string"}},
            "required": ["equipment_tag"],
        },
    },
    "tareas": {
        "description": "Catálogo de tareas, opcionalmente por equipo.",
        "inputSchema": {
            "type": "object",
            "properties": {"equipment_tag": {"type": "string"}},
        },
    },
    "manuales": {
        "description": "Búsqueda en los manuales del fabricante.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "equipment_tag": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["question"],
        },
    },
}

_QUERY_MODELS = {
    "equipos": (EquipmentQuery, "equipment"),
    "historial_sensores": (SensorHistoryQuery, "sensor_history"),
    "historial_ordenes": (OrderHistoryQuery, "order_history"),
    "inventario": (InventoryQuery, "inventory"),
    "materiales": (MaterialListQuery, "materials"),
    "tareas": (TaskCatalogQuery, "tasks"),
    "manuales": (ManualSearchQuery, "manuals"),
}


class EquipmentMCPServer:
    """Superficie MCP: expone las tools de solo lectura por JSON-RPC (stdio)."""

    name = "planta-equipment"
    version = "0.1.0"

    def __init__(self, tools: ReadOnlyTools) -> None:
        self.tools = tools

    def list_tools(self) -> list[str]:
        return list(_QUERY_MODELS)

    def tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "description": _TOOL_SCHEMAS[name]["description"],
                "inputSchema": _TOOL_SCHEMAS[name]["inputSchema"],
            }
            for name in _QUERY_MODELS
        ]

    def call(self, name: str, arguments: dict[str, Any]) -> list[Any]:
        if name not in _QUERY_MODELS:
            raise ValueError(f"Tool MCP inexistente: {name}")
        model, handler_name = _QUERY_MODELS[name]
        handler = getattr(self.tools, handler_name)
        return handler(model.model_validate(arguments or {}))

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Procesa un mensaje JSON-RPC 2.0 del cliente MCP y devuelve la respuesta."""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            return _response(msg_id, {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return _response(msg_id, {"tools": self.tool_schemas()})
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                result = self.call(name, arguments)
                text = json.dumps(_to_json(result), ensure_ascii=False)
                return _response(msg_id, {
                    "content": [{"type": "text", "text": text}],
                    "isError": False,
                })
            except Exception as exc:
                return _response(msg_id, {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                })
        return _error(msg_id, -32601, f"Method not found: {method}")

    def run_stdio(self) -> None:
        """Transporte stdio: lee mensajes JSON-RPC de stdin y escribe en stdout."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            response = self.handle_message(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, default=str) + "\n")
                sys.stdout.flush()


def _response(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _to_json(value: Any) -> Any:
    """Convierte modelos Pydantic y datetimes a objetos serializables."""
    if isinstance(value, list):
        return [_to_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_json(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def serve_stdio(server: EquipmentMCPServer) -> None:
    server.run_stdio()


def build_server() -> EquipmentMCPServer:
    """Arma un servidor MCP con los datos locales (sin MQTT ni base)."""
    from .domain import DomainService
    from .official_data import catalog_from_materials, equipment_from_definition, load_material_catalog, load_yaml

    service = DomainService()
    try:
        for equipment in equipment_from_definition(load_yaml("datos/planta.yaml")):
            service.add_equipment(equipment)
        inventory, materials, tasks = catalog_from_materials(
            load_material_catalog("datos/materiales.yaml")
        )
        service.inventory_catalog = inventory
        service.material_catalog = materials
        service.task_catalog = tasks
    except FileNotFoundError:
        pass
    return EquipmentMCPServer(ReadOnlyTools(service))


if __name__ == "__main__":
    build_server().run_stdio()
