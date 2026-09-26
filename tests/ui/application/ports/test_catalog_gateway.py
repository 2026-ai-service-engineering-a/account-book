from __future__ import annotations

import inspect

from ui.application.ports import CatalogGateway
from ui.infrastructure.memory import MemoryCatalogGateway


def test_stand_in_fills_the_port(store):
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: CatalogGateway = MemoryCatalogGateway(store)
    for method in ("categories", "accounts"):
        assert inspect.iscoroutinefunction(getattr(port, method)), method
