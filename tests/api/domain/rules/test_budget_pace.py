from __future__ import annotations

from datetime import date

from api.domain.rules import budget_pace as pace
from api.domain.values import Money, Period

SEPT = Period(2026, 9)


def test_elapsed_days_past_current_future():
    assert pace.elapsed_days(SEPT, date(2026, 10, 1)) == 30
    assert pace.elapsed_days(SEPT, date(2026, 9, 17)) == 17
    assert pace.elapsed_days(SEPT, date(2026, 8, 31)) == 0


def test_cumulative_fills_quiet_days():
    series = pace.cumulative([(2, Money(100)), (2, Money(50)), (4, Money(10))], through=4)
    assert series == (Money(0), Money(150), Money(150), Money(160))


def test_projection_is_whole_won_rounded_down():
    assert pace.project(Money(1000), elapsed=3, days=30) == Money(10_000)
    assert pace.project(Money(100), elapsed=0, days=30) == Money(100)


def test_crossing_day_already_over_or_projected():
    over = (Money(100), Money(400))
    assert pace.crossing_day(over, Money(300), 30) == 2
    on_pace = tuple(Money(10 * d) for d in range(1, 11))  # 하루 10원
    assert pace.crossing_day(on_pace, Money(200), 30) == 21
    assert pace.crossing_day(on_pace, Money(1000), 30) is None  # 말일까지 안 넘는다


def test_day_in():
    assert pace.day_in(SEPT, 21) == date(2026, 9, 21) and pace.day_in(SEPT, None) is None
