from __future__ import annotations

from ui.application.dto import Direction, Period, TransactionFilter


def test_period_alone_is_not_narrowed():
    assert not TransactionFilter(Period(2026, 9)).is_narrowed


def test_any_other_condition_narrows():
    assert TransactionFilter(Period(2026, 9), direction=Direction.INCOME).is_narrowed
    assert TransactionFilter(Period(2026, 9), query="스타").is_narrowed
