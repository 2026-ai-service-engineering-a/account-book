from __future__ import annotations

from api.application.ports import StatsRepository
from tests.api.conftest import FakeStats, FakeTransactions


def test_fake_fills_the_port():
    port: StatsRepository = FakeStats(FakeTransactions())
    assert port is not None
