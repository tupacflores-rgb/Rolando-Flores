from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import yaml

from .models import Equipment


def load_yaml(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Archivo de datos inexistente: {source}")
    with source.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"El archivo no contiene un objeto YAML: {source}")
    return data


def equipment_from_definition(data: dict[str, Any]) -> list[Equipment]:
    if not isinstance(data, dict):
        raise ValueError("La definición de planta no es un objeto")
    result: list[Equipment] = []
    limits: dict[str, dict[str, float | None]] = {}
    sensor_groups: dict[str, list[dict[str, Any]]] = {}
    for sensor in data.get("sensores", []):
        if isinstance(sensor, dict):
            sensor_groups.setdefault(sensor["tag"], []).append(sensor)
    for tag, sensors in sensor_groups.items():
        selected = next(
            (item for item in sensors if item["variable"] == "presion_descarga"),
            next(
                (item for item in sensors if item["variable"] == "presion_diferencial"),
                sensors[0],
            ),
        )
        limits[tag] = {
            "min": selected.get("alarma_baja"),
            "max": selected.get("alarma_alta"),
        }
    for item in data.get("equipos", []):
        if not isinstance(item, dict):
            raise ValueError("Entrada de equipo inválida")
        result.append(
            Equipment(
                tag=item["tag"],
                name=item["descripcion"],
                aliases=item.get("nombres", []),
                kind=item["tipo"],
                alarm_min=limits.get(item["tag"], {}).get("min"),
                alarm_max=limits.get(item["tag"], {}).get("max"),
                reserve_available=item.get("rol_inicial") == "reserva",
            )
        )
    return result


def load_equipment(path: str | Path) -> list[Equipment]:
    return equipment_from_definition(load_yaml(path))


def load_material_catalog(path: str | Path) -> dict[str, Any]:
    data = load_yaml(path)
    required = {"repuestos", "lista_materiales", "tareas_estandar"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Faltan secciones de materiales: {sorted(missing)}")
    return data


def load_voice_index(path: str | Path) -> dict[str, dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Índice de voces inexistente: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"El índice de voces no es un objeto: {source}")
    return data
