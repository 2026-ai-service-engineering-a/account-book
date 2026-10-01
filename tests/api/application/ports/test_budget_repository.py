from __future__ import annotations

from api.application.ports import BudgetRepository
from tests.api.conftest import FakeBudgets


def test_fake_fills_the_port():
    port: BudgetRepository = FakeBudgets()
    assert port is not None
