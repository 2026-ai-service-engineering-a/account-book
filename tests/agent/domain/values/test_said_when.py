from __future__ import annotations

from datetime import datetime

import pytest

from agent.domain.values import SaidDay, SaidWhen
from tests.agent.conftest import NOW, SEOUL


def at(month: int, day: int, hour: int, minute: int = 0, year: int = 2026) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=SEOUL)


def test_nothing_said_fills_nothing():
    # 폼에 이미 있는 값(지금)이 남는다
    assert SaidWhen().resolve(NOW) is None


def test_time_without_day_is_today():
    assert SaidWhen(hour=15).resolve(NOW) == at(10, 1, 15)


def test_today_without_time_is_now_to_the_minute():
    now = NOW.replace(minute=7, second=42, microsecond=9)
    assert SaidWhen(day=SaidDay.TODAY).resolve(now) == at(10, 1, 18, 7)


@pytest.mark.parametrize(
    ("day", "expected"),
    [(SaidDay.YESTERDAY, at(9, 30, 12)), (SaidDay.DAY_BEFORE_YESTERDAY, at(9, 29, 12))],
)
def test_past_day_without_time_is_noon(day, expected):
    # 한낮에 두면 타임존이 달라도 날짜가 넘어가지 않는다
    assert SaidWhen(day=day).resolve(NOW) == expected


def test_yesterday_with_time():
    assert SaidWhen(day=SaidDay.YESTERDAY, hour=21, minute=30).resolve(NOW) == at(9, 30, 21, 30)


def test_month_day_is_this_year_when_already_past():
    when = SaidWhen(day=SaidDay.DATE, month=9, day_of_month=16, hour=12, minute=31)
    assert when.resolve(NOW) == at(9, 16, 12, 31)


def test_month_day_after_now_is_last_year():
    # 12/31 문자를 1/2에 붙여넣는 경우
    when = SaidWhen(day=SaidDay.DATE, month=12, day_of_month=31, hour=23)
    assert when.resolve(NOW) == at(12, 31, 23, year=2025)


def test_impossible_date_fills_nothing():
    assert SaidWhen(day=SaidDay.DATE, month=2, day_of_month=30).resolve(NOW) is None


def test_keeps_the_callers_zone():
    resolved = SaidWhen(hour=9).resolve(NOW)
    assert resolved is not None and resolved.tzinfo is SEOUL


def test_needs_an_aware_now():
    with pytest.raises(ValueError):
        SaidWhen(hour=9).resolve(datetime(2026, 10, 1, 18))


@pytest.mark.parametrize(
    "fields",
    [
        {"hour": 24},
        {"hour": 9, "minute": 60},
        {"day": SaidDay.DATE, "month": 13, "day_of_month": 1},
        {"day": SaidDay.DATE, "month": 9, "day_of_month": 0},
    ],
)
def test_rejects_what_is_not_a_time(fields):
    with pytest.raises(ValueError):
        SaidWhen(**fields)
