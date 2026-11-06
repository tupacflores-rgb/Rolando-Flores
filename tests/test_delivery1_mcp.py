"""Tests de la Entrega 1: servidor MCP (P4)."""

import json

from app.domain import DomainService
from app.mcp import EquipmentMCPServer
from app.models import Equipment
from app.tools import ReadOnlyTools


def _server():
    service = DomainService()
    service.add_equipment(Equipment(tag="B-101", name="Bomba 1", kind="bomba", aliases=["la uno"]))
    return EquipmentMCPServer(ReadOnlyTools(service))


def test_mcp_initialize():
    server = _server()
    response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in response["result"]["capabilities"]


def test_mcp_tools_list():
    server = _server()
    response = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert "equipos" in names
    assert "inventario" in names
    assert "historial_sensores" in names


def test_mcp_tools_call():
    server = _server()
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "equipos", "arguments": {}},
    })
    assert response["result"]["isError"] is False
    content = json.loads(response["result"]["content"][0]["text"])
    assert any(item["tag"] == "B-101" for item in content)


def test_mcp_unknown_tool_is_error():
    server = _server()
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "no-existe", "arguments": {}},
    })
    assert response["result"]["isError"] is True


def test_mcp_unknown_method():
    server = _server()
    response = server.handle_message({"jsonrpc": "2.0", "id": 5, "method": "ping", "params": {}})
    assert response["error"]["code"] == -32601
