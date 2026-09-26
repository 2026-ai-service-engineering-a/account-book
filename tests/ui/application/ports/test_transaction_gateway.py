from __future__ import annotations

import inspect

from ui.application.ports import TransactionGateway
from ui.infrastructure.memory import MemoryTransactionGateway


def test_stand_in_fills_the_port(store):
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: TransactionGateway = MemoryTransactionGateway(store)
    for method in ("exists_any", "search", "get", "create", "update", "delete"):
        assert inspect.iscoroutinefunction(getattr(port, method)), method
