from __future__ import annotations

from datetime import datetime
from typing import Any


def load_contract() -> Any:
    """Carga el contrato oficial instalado, sin copiar sus modelos al proyecto."""
    try:
        import planta_contrato
    except ImportError as exc:
        raise RuntimeError(
            "Falta instalar planta_contrato; no se permite usar una copia local del contrato"
        ) from exc
    return planta_contrato


def heartbeat(sistema: str, enlace_ok: bool, pendientes: int) -> dict[str, Any]:
    contract = load_contract()
    return contract.EstadoSistema(
        ts=datetime.now().astimezone(),
        sistema=sistema,
        enlace_ok=enlace_ok,
        pendientes_sincronizar=pendientes,
    ).model_dump(mode="json")


def topic(name: str, **values: str) -> str:
    contract = load_contract()
    template = getattr(contract.Topicos, name.upper())
    return template.format(**values)
