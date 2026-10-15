from __future__ import annotations

import inspect

from ui.application.ports import RunGateway
from ui.infrastructure.api import ApiClient, HttpRunGateway
from ui.infrastructure.memory import MemoryRunGateway


def test_both_fill_the_port_and_neither_writes():
    # 대입이 곧 계약 검사다. 읽기만 하는 포트라 쓰는 메서드가 없다
    for port in (MemoryRunGateway(), HttpRunGateway(ApiClient("http://api", timeout=1))):
        checked: RunGateway = port
        for method in ("page", "get"):
            assert inspect.iscoroutinefunction(getattr(checked, method)), method
    public = {n for n in dir(RunGateway) if not n.startswith("_")}
    assert public == {"page", "get"}
