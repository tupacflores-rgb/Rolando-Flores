from __future__ import annotations

from uuid import UUID

from .models import ClosureComparison, ClosureReport, Habilita, Order


def compare_closure(order: Order, closure: ClosureReport) -> ClosureComparison:
    expected_tasks = {order.task}
    expected_parts = set(order.parts)
    tasks_done = set(closure.tasks_done)
    parts_used = set(closure.parts_used)
    missing_tasks = sorted(expected_tasks - tasks_done)
    unexpected_tasks = sorted(tasks_done - expected_tasks)
    missing_parts = sorted(expected_parts - parts_used)
    unexpected_parts = sorted(parts_used - expected_parts)
    differences = [
        *(f"Tarea faltante: {item}" for item in missing_tasks),
        *(f"Tarea no solicitada: {item}" for item in unexpected_tasks),
        *(f"Repuesto faltante: {item}" for item in missing_parts),
        *(f"Repuesto no reservado: {item}" for item in unexpected_parts),
    ]
    return ClosureComparison(
        order_id=order.id,
        missing_tasks=missing_tasks,
        unexpected_tasks=unexpected_tasks,
        missing_parts=missing_parts,
        unexpected_parts=unexpected_parts,
        differences=differences,
        matches=not differences,
    )


def issue_habilita(order: Order, contract_prices: dict[str, float]) -> Habilita:
    amount = sum(contract_prices.get(part, 0.0) for part in order.parts)
    return Habilita(
        number=f"HAB-{str(order.id)[:8].upper()}",
        order_id=UUID(str(order.id)),
        amount_usd=amount,
    )
