from __future__ import annotations

from datetime import date

import pytest

from ui.application.dto import Period


def test_parse_accepts_year_month():
    assert Period.parse("2026-09") == Period(2026, 9)


@pytest.mark.parametrize("text", ["2026-13", "2026-9", "abc", "", "2026-00"])
def test_parse_rejects_malformed(text):
    assert Period.parse(text) is None


def test_previous_and_next_cross_year():
    assert Period(2026, 1).previous() == Period(2025, 12)
    assert Period(2025, 12).next() == Period(2026, 1)


def test_days_knows_leap_year():
    assert Period(2028, 2).days == 29
    assert Period(2026, 2).days == 28


def test_str_round_trips():
    assert Period.parse(str(Period(2026, 3))) == Period(2026, 3)


def test_contains():
    assert Period(2026, 9).contains(date(2026, 9, 30))
    assert not Period(2026, 9).contains(date(2026, 10, 1))
