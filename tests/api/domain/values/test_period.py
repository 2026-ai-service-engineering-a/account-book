from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from api.domain.values import Period

SEOUL = ZoneInfo("Asia/Seoul")


def test_parse_and_print():
    assert str(Period.parse("2026-09")) == "2026-09"


@pytest.mark.parametrize("bad", ["2026-13", "2026-9", "26-09", ""])
def test_rejects_what_is_not_a_month(bad):
    with pytest.raises(ValueError):
        Period.parse(bad)


def test_bounds_are_half_open_in_the_users_zone():
    # 2026-09월 = [2026-09-01T00:00+09:00, 2026-10-01T00:00+09:00) (development-rules 6.1)
    start, end = Period(2026, 9).bounds(SEOUL)
    assert start == datetime(2026, 8, 31, 15, tzinfo=UTC)
    assert end == datetime(2026, 9, 30, 15, tzinfo=UTC)


def test_year_boundaries():
    assert Period(2026, 1).previous() == Period(2025, 12)
    assert Period(2025, 12).next() == Period(2026, 1)
    assert Period(2026, 2).days == 28
