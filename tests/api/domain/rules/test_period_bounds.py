from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from api.domain.rules import period_bounds
from api.domain.values import Period, TimeRange

SEOUL = ZoneInfo("Asia/Seoul")


def test_month_is_resolved_in_the_users_zone():
    assert period_bounds.bounds(Period(2026, 9), SEOUL) == (
        datetime(2026, 8, 31, 15, tzinfo=UTC),
        datetime(2026, 9, 30, 15, tzinfo=UTC),
    )


def test_range_is_taken_as_given():
    week = TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL))
    assert period_bounds.bounds(week, SEOUL) == (week.start, week.end)


def test_nothing_means_no_bounds():
    assert period_bounds.bounds(None, SEOUL) == (None, None)
