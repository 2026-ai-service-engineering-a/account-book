from __future__ import annotations

from api.application.ports import InsightCache
from tests.api.fakes import FakeInsightCache


def test_fake_fills_the_port():
    port: InsightCache = FakeInsightCache()
    assert port.get("k") is None
