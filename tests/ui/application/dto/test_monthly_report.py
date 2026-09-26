from __future__ import annotations

from ui.application.dto import MonthlyReport, Period, Totals
from ui.application.values import Money


def report(expense, income):
    return MonthlyReport(Period(2026, 9), Totals(Money(expense), Money(income)), None, (), (), None)


def test_empty_only_without_any_money():
    assert report(0, 0).is_empty
    assert not report(0, 3_200_000).is_empty
    assert not report(8_500, 0).is_empty
