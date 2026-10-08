from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from agent.domain.values import PeriodName, PeriodSpec
from tests.agent.conftest import SEOUL

THURSDAY = date(2026, 10, 8)  # 이번 주 월요일은 10/5


def days(spec: PeriodSpec, today: date = THURSDAY) -> tuple[date, date]:
    """경계를 사용자 타임존의 날짜로 — [첫날, 끝 다음 날)."""
    found = spec.bounds(today, SEOUL)
    return found.start.date(), found.end.date()


@pytest.mark.parametrize(
    ("spec", "first", "after"),
    [
        (PeriodSpec(PeriodName.TODAY), date(2026, 10, 8), date(2026, 10, 9)),
        (PeriodSpec(PeriodName.YESTERDAY), date(2026, 10, 7), date(2026, 10, 8)),
        (PeriodSpec(PeriodName.THIS_WEEK), date(2026, 10, 5), date(2026, 10, 9)),
        (PeriodSpec(PeriodName.LAST_WEEK), date(2026, 9, 28), date(2026, 10, 5)),
        (PeriodSpec(PeriodName.THIS_MONTH), date(2026, 10, 1), date(2026, 11, 1)),
        (PeriodSpec(PeriodName.LAST_MONTH), date(2026, 9, 1), date(2026, 10, 1)),
        (PeriodSpec(PeriodName.THIS_YEAR), date(2026, 1, 1), date(2026, 10, 9)),
        (PeriodSpec(PeriodName.LAST_N_DAYS, days=3), date(2026, 10, 6), date(2026, 10, 9)),
        (PeriodSpec(PeriodName.MONTH, start=date(2026, 8, 1)), date(2026, 8, 1), date(2026, 9, 1)),
        (
            PeriodSpec(PeriodName.RANGE, start=date(2026, 9, 3), end=date(2026, 9, 10)),
            date(2026, 9, 3),
            date(2026, 9, 11),  # 끝 날짜(9/10)도 들어간다
        ),
    ],
)
def test_the_table_in_chat_analytics(spec, first, after):
    assert days(spec) == (first, after)


def test_bounds_are_midnight_in_the_users_zone():
    week = PeriodSpec(PeriodName.LAST_WEEK).bounds(THURSDAY, SEOUL)
    assert week.start == datetime(2026, 9, 27, 15, tzinfo=UTC)  # 서울 9/28 00:00
    assert week.end == datetime(2026, 10, 4, 15, tzinfo=UTC)  # 서울 10/5 00:00 — 열린 끝


def test_week_starts_on_monday_and_last_week_never_holds_today():
    monday, sunday = date(2026, 10, 5), date(2026, 10, 11)
    assert days(PeriodSpec(PeriodName.THIS_WEEK), monday) == (monday, date(2026, 10, 6))
    assert days(PeriodSpec(PeriodName.LAST_WEEK), monday) == (date(2026, 9, 28), monday)
    assert days(PeriodSpec(PeriodName.THIS_WEEK), sunday) == (monday, date(2026, 10, 12))


def test_year_edges():
    assert days(PeriodSpec(PeriodName.LAST_MONTH), date(2026, 1, 15)) == (
        date(2025, 12, 1),
        date(2026, 1, 1),
    )
    assert days(PeriodSpec(PeriodName.THIS_MONTH), date(2026, 12, 31)) == (
        date(2026, 12, 1),
        date(2027, 1, 1),
    )


@pytest.mark.parametrize(
    "build",
    [
        lambda: PeriodSpec(PeriodName.LAST_N_DAYS),  # n이 없다
        lambda: PeriodSpec(PeriodName.LAST_N_DAYS, days=0),
        lambda: PeriodSpec(PeriodName.LAST_N_DAYS, days=366),
        lambda: PeriodSpec(PeriodName.TODAY, days=3),  # 쓰지 않는 값이 붙었다
        lambda: PeriodSpec(PeriodName.MONTH),
        lambda: PeriodSpec(PeriodName.MONTH, start=date(2026, 8, 2)),
        lambda: PeriodSpec(PeriodName.RANGE, start=date(2026, 9, 3)),
        lambda: PeriodSpec(PeriodName.RANGE, start=date(2026, 9, 10), end=date(2026, 9, 3)),
        lambda: PeriodSpec(PeriodName.RANGE, start=date(2023, 1, 1), end=date(2026, 1, 1)),
        lambda: PeriodSpec(PeriodName.THIS_MONTH, end=date(2026, 9, 3)),
    ],
)
def test_rejects_values_the_name_does_not_take(build):
    with pytest.raises(ValueError):
        build()
