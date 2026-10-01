from __future__ import annotations

from datetime import datetime

from api.application.use_cases import BuildMonthlyReport
from api.domain.values import Money, Period
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL, FixedClock

CLOCK = FixedClock(datetime(2026, 9, 17, 18, tzinfo=SEOUL))


def test_compares_with_last_month_by_category():
    report = BuildMonthlyReport(ledger(), CLOCK)(Period(2026, 9))
    assert report.totals.expense == Money(185_000) and report.previous is not None
    food = next(c for c in report.by_category if c.category.id == "food")
    assert (food.this_month, food.last_month, food.delta) == (
        Money(180_000),
        Money(30_000),
        Money(150_000),
    )
    assert food.percent == 500
    assert [c.category.id for c in report.by_category] == ["food", "cafe"]  # 큰 순서
    assert [str(m.period) for m in report.months] == ["2026-08", "2026-09"]
    assert report.through_day == 17  # 진행 중인 달


def test_first_month_has_nothing_to_compare_with():
    report = BuildMonthlyReport(ledger(), CLOCK)(Period(2026, 8))
    assert report.previous is None and report.by_category[0].last_month is None
    assert report.through_day is None
