from __future__ import annotations

from datetime import date

from agent.domain.values import Amount
from agent.infrastructure.http.budget_status_reply import BudgetStatusReply

FOOD = {
    "category": {"id": "food", "name": "식비", "direction": "expense"},
    "limit": 300000,
    "spent": 182300,
    "remaining": 117700,
    "percent": 61,
    "projected": 332000,
    "over_on": "2026-09-28",
}
CAFE = {
    "category": {"id": "cafe", "name": "카페", "direction": "expense"},
    "limit": None,
    "spent": 6300,
    "remaining": None,
    "percent": None,
    "projected": None,
}


def test_budget_and_no_budget():
    food, cafe = BudgetStatusReply.model_validate([FOOD, CAFE | {"over_on": None}]).lines()
    assert (food.limit, food.projected, food.over_on) == (
        Amount(300000),
        Amount(332000),
        date(2026, 9, 28),
    )
    assert cafe.limit is None and cafe.spent == Amount(6300)
