from __future__ import annotations

from datetime import date

from tests.ui.infrastructure.api.conftest import STATUS
from ui.application.values import Money
from ui.infrastructure.api import BudgetStatusReply


def test_becomes_a_ui_status():
    status = BudgetStatusReply.model_validate(STATUS).status()
    assert status.limit == Money(300000) and status.over_on == date(2026, 9, 6)
    empty = BudgetStatusReply.model_validate(STATUS | {"limit": None, "remaining": None}).status()
    assert empty.limit is None
