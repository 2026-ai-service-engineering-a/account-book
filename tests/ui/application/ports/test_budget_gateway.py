from __future__ import annotations

import inspect

from ui.application.ports import BudgetGateway
from ui.infrastructure.memory import MemoryBudgetGateway


def test_stand_in_fills_the_port(store, clock):
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: BudgetGateway = MemoryBudgetGateway(store, clock)
    for method in ("statuses", "status", "set_limit"):
        assert inspect.iscoroutinefunction(getattr(port, method)), method
