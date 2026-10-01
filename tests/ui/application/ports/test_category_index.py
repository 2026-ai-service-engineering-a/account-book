from __future__ import annotations

import inspect

from tests.ui.conftest import SEOUL
from ui.application.ports import CategoryIndex
from ui.infrastructure.memory import MemoryCategoryIndex, MemoryStore


def test_memory_stand_in_fills_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: CategoryIndex = MemoryCategoryIndex(MemoryStore.create(SEOUL), top_k=8, temperature=0.03)
    assert inspect.iscoroutinefunction(port.suggest)
