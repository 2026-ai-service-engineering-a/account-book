from __future__ import annotations

from api.application.dto import MonthTotal
from api.domain.values import Money, Period
from api.interfaces.schemas import MonthTotalBody


def test_period_as_text():
    body = MonthTotalBody.of(MonthTotal(Period(2026, 9), Money(1), Money(2))).model_dump()
    assert body == {"period": "2026-09", "expense": 1, "income": 2}
