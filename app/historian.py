"""Cliente del historiador oficial de la planta (solo lectura, con caché).

El historiador (``GET /api/historian/{tag}/{variable}`` y
``GET /api/historial-ordenes``) vive en la planta simulada. Este cliente lo
consulta por HTTP y conserva la última respuesta en caché: si el enlace está
caído, devuelve el último valor conocido en lugar de fallar o devolver listas
vacías en silencio.
"""

from __future__ import annotations

from typing import Any

import httpx


class HistorianClient:
    """Consulta el historiador oficial; degrada a caché si no hay enlace."""

    def __init__(self, base_url: str | None = None, *, transport: Any = None) -> None:
        self.base_url = (base_url or "").strip().rstrip("/")
        self._transport = transport or httpx
        self._sensor_cache: dict[tuple[str, str], list[dict]] = {}
        self._orders_cache: dict[str, list[dict]] = {}
        self.sensor_error: str | None = None
        self.orders_error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    def sensor_history(self, tag: str, variable: str) -> list[dict]:
        key = (tag, variable)
        if not self.base_url:
            return list(self._sensor_cache.get(key, []))
        try:
            response = self._transport.get(
                f"{self.base_url}/api/historian/{tag}/{variable}", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                self._sensor_cache[key] = data
                self.sensor_error = None
                return data
        except Exception as exc:  # enlace caído o respuesta inválida
            self.sensor_error = str(exc)
        return list(self._sensor_cache.get(key, []))

    def order_history(self, equipment_tag: str | None = None) -> list[dict]:
        key = equipment_tag or ""
        if not self.base_url:
            return list(self._orders_cache.get(key, []))
        url = f"{self.base_url}/api/historial-ordenes"
        if equipment_tag:
            url += f"?equipo={equipment_tag}"
        try:
            response = self._transport.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                self._orders_cache[key] = data
                self.orders_error = None
                return data
        except Exception as exc:
            self.orders_error = str(exc)
        return list(self._orders_cache.get(key, []))


def build_historian(base_url: str | None) -> HistorianClient:
    return HistorianClient(base_url)
