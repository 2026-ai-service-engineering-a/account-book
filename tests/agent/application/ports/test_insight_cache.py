from __future__ import annotations

import inspect

from agent.application.ports import InsightCache
from agent.infrastructure.http import HttpInsightCache
from tests.agent.conftest import FakeInsightCache


def test_adapter_and_fake_fill_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    real: InsightCache = HttpInsightCache("http://api:8000", timeout=1)
    fake: InsightCache = FakeInsightCache()
    assert inspect.iscoroutinefunction(real.get) and inspect.iscoroutinefunction(fake.put)
