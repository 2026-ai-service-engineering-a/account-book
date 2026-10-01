from __future__ import annotations

from datetime import date, datetime

from api.application.use_cases import ReadPace
from api.domain.values import CategoryId, Money, Period
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL, FixedClock


def test_cumulative_up_to_today():
    clock = FixedClock(datetime(2026, 9, 3, 18, tzinfo=SEOUL))
    series = ReadPace(ledger(), clock)(CategoryId("food"), Period(2026, 9))
    assert series is not None
    assert series.cumulative == (Money(100_000), Money(180_000), Money(180_000))
    assert series.over_on == date(2026, 9, 6) and series.days_in_month == 30


def test_none_without_a_budget_or_for_a_month_not_started():
    clock = FixedClock(datetime(2026, 9, 3, tzinfo=SEOUL))
    assert ReadPace(ledger(), clock)(CategoryId("cafe"), Period(2026, 9)) is None
    assert ReadPace(ledger(), clock)(CategoryId("food"), Period(2026, 10)) is None
