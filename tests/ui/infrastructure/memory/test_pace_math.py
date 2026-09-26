from __future__ import annotations

from datetime import date

from ui.application.dto import Period
from ui.application.values import Money
from ui.infrastructure.memory import pace_math


def won(*amounts):
    return tuple(Money(a) for a in amounts)


def test_elapsed_days_by_month_position():
    today = date(2026, 9, 17)
    assert pace_math.elapsed_days(Period(2026, 9), today) == 17
    assert pace_math.elapsed_days(Period(2026, 8), today) == 31
    assert pace_math.elapsed_days(Period(2026, 10), today) == 0


def test_cumulative_fills_quiet_days():
    rows = [(1, Money(100)), (3, Money(50)), (3, Money(50))]
    assert pace_math.cumulative(rows, 4) == won(100, 100, 200, 200)


def test_project_scales_to_month():
    assert pace_math.project(Money(182_300), 17, 30) == Money(321_705)


def test_crossing_day_already_over():
    assert pace_math.crossing_day(won(50, 120, 130), limit=Money(100), days=30) == 2


def test_crossing_day_projected():
    # 하루 10씩이면 100을 넘는 첫 날은 11일
    assert pace_math.crossing_day(won(10, 20, 30), limit=Money(100), days=30) == 11


def test_crossing_day_none_when_pace_is_safe():
    assert pace_math.crossing_day(won(1, 2, 3), limit=Money(100), days=30) is None
