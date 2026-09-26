from __future__ import annotations

import inspect

from ui.application.ports import DemoData
from ui.infrastructure.memory import MemoryDemoData


def test_stand_in_fills_the_port(store, clock):
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: DemoData = MemoryDemoData(store, clock)
    for method in ("reset",):
        assert inspect.iscoroutinefunction(getattr(port, method)), method
