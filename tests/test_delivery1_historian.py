"""Tests de la Entrega 1: historial de sensores y órdenes (P3)."""

from datetime import UTC, datetime

from app.historian import HistorianClient
from app.models import SensorReading
from app.tools import OrderHistoryQuery, ReadOnlyTools, SensorHistoryQuery
from app.domain import DomainService


class FakeHistorian:
    """Historiador en memoria para las pruebas; simula el enlace caído."""

    def __init__(self, sensors=None, orders=None, *, down=False):
        self._sensors = sensors or {}
        self._orders = orders or {}
        self.down = down
        self.sensor_error = None
        self.orders_error = None

    def sensor_history(self, tag, variable):
        if self.down:
            self.sensor_error = "enlace caído"
            return []
        return list(self._sensors.get((tag, variable), []))

    def order_history(self, equipment_tag=None):
        if self.down:
            self.orders_error = "enlace caído"
            return []
        return list(self._orders.get(equipment_tag or "", []))


def _service():
    return DomainService()


def test_sensor_history_multiple_readings():
    service = _service()
    historian = FakeHistorian(
        sensors={
            ("B-101", "presion_descarga"): [
                {"ts": "2026-11-01T10:00:00Z", "valor": 110.0},
                {"ts": "2026-11-01T10:01:00Z", "valor": 112.0},
            ]
        }
    )
    tools = ReadOnlyTools(service, historian)
    result = tools.sensor_history(SensorHistoryQuery(tag="B-101", variable="presion_descarga"))
    assert len(result) >= 2
    assert {r["value"] for r in result} == {110.0, 112.0}


def test_order_history_with_simulator_data():
    service = _service()
    historian = FakeHistorian(
        orders={
            "": [
                {"numero": "OT-25-0001", "equipo": "B-101", "tareas": ["T-B-VAL"], "origen": "archivo"},
                {"numero": "OT-26-0002", "equipo": "B-102", "tareas": ["T-B-COR"], "origen": "simulador"},
            ]
        }
    )
    tools = ReadOnlyTools(service, historian)
    result = tools.order_history(OrderHistoryQuery(equipment_tag=None))
    assert len(result) == 2
    assert any(r.get("origen") == "simulador" for r in result)


def test_historian_fallback_when_link_down():
    service = _service()
    service.sensor_readings["s-1"] = SensorReading(
        idempotency_key="s-1",
        equipment_tag="B-101",
        variable="presion_descarga",
        value=115,
        unit="kg/cm2",
        observed_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC),
    )
    historian = FakeHistorian(down=True)
    tools = ReadOnlyTools(service, historian)
    result = tools.sensor_history(SensorHistoryQuery(tag="B-101", variable="presion_descarga"))
    # Sin historiador disponible, cae a las lecturas locales (no devuelve vacío en silencio).
    assert len(result) >= 1
    assert result[0]["value"] == 115


def test_historian_client_http_fallback_uses_cache():
    class Boom:
        def get(self, *args, **kwargs):
            raise RuntimeError("no route to host")

    client = HistorianClient("http://sim:8100", transport=Boom())
    # Primera llamada: sin caché, devuelve vacío y registra el error.
    assert client.sensor_history("B-101", "presion_descarga") == []
    assert client.sensor_error is not None
    # Caché a mano: la próxima llamada (aunque siga caído) devuelve lo conocido.
    client._sensor_cache[("B-101", "presion_descarga")] = [{"ts": "x", "valor": 120}]
    assert client.sensor_history("B-101", "presion_descarga") == [{"ts": "x", "valor": 120}]
