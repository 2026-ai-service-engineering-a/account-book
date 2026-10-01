from __future__ import annotations

from api.application.dto import MonthlyReport, Totals
from api.domain.values import Money, Period
from api.interfaces.schemas import MonthlyReportBody


def test_previous_is_null_on_the_first_month():
    report = MonthlyReport(Period(2026, 9), Totals(Money(1), Money(0)), None, (), (), 17)
    body = MonthlyReportBody.of(report).model_dump()
    assert body["previous"] is None and body["through_day"] == 17
