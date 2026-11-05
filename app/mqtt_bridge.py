from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .contract_adapter import heartbeat, load_contract, topic


class MqttBridge:
    """Puente explícito entre el contrato oficial y el dominio de la planta."""

    def __init__(
        self,
        *,
        on_recorrida: Callable[[dict[str, Any]], None],
        on_sensor: Callable[[dict[str, Any]], None],
        on_cierre: Callable[[dict[str, Any]], None],
        on_respuesta: Callable[[dict[str, Any]], None],
        client: Any | None = None,
    ) -> None:
        self.callbacks = {
            "recorrida": on_recorrida,
            "sensor": on_sensor,
            "cierre": on_cierre,
            "respuesta": on_respuesta,
        }
        self.client = client or self._new_client()
        self.errors: list[str] = []

    @staticmethod
    def _new_client() -> Any:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("Instalá paho-mqtt para conectar con el broker oficial") from exc
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def start(self, host: str = "broker", port: int = 1883) -> None:
        self.client.on_message = self._on_message
        self.client.connect(host, port, keepalive=30)
        contract = load_contract()
        subscriptions = (
            contract.Topicos.RECORRIDAS,
            contract.Topicos.SENSORES,
            contract.Topicos.CIERRES,
            contract.Topicos.RESPUESTAS,
        )
        for subscription in subscriptions:
            self.client.subscribe(subscription)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def _on_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            kind = self._kind_for_topic(message.topic)
            self.callbacks[kind](payload)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
            self.errors.append(f"Mensaje MQTT rechazado: {exc}")
        except Exception as exc:
            self.errors.append(f"Error procesando mensaje MQTT: {exc}")

    @staticmethod
    def _kind_for_topic(message_topic: str) -> str:
        contract = load_contract()
        if message_topic == contract.Topicos.RECORRIDAS:
            return "recorrida"
        if message_topic.startswith("planta/sensores/"):
            return "sensor"
        if message_topic == contract.Topicos.CIERRES:
            return "cierre"
        if message_topic == contract.Topicos.RESPUESTAS:
            return "respuesta"
        raise ValueError(f"Topic MQTT no soportado: {message_topic}")

    def publish_heartbeat(
        self, sistema: str, enlace_ok: bool, pendientes: int
    ) -> None:
        self.client.publish(
            topic("ESTADO"),
            json.dumps(heartbeat(sistema, enlace_ok, pendientes)),
            qos=1,
            retain=True,
        )

    def publish_tablet(self, payload: dict[str, Any]) -> None:
        self.client.publish(
            topic("TABLET"),
            json.dumps(payload),
            qos=1,
            retain=False,
        )
