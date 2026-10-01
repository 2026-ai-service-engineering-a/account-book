from __future__ import annotations

from tests.agent.conftest import evidence


def test_amount_is_money_and_day_is_a_date():
    item = evidence("t1", "스타벅스", "cafe", 0.7)
    assert item.amount.amount == 5800 and item.day.isoformat() == "2026-09-12"
