from __future__ import annotations

from datetime import date

from api.application.dto import BudgetStatus
from api.domain.entities import Category
from api.domain.values import CategoryId, Direction, Money
from api.interfaces.schemas import BudgetStatusBody

FOOD = Category(CategoryId("food"), "식비", Direction.EXPENSE)


def test_no_budget_is_all_nulls_but_spent():
    body = BudgetStatusBody.of(BudgetStatus(FOOD, None, Money(10), None, None, None, None))
    assert body.model_dump()["limit"] is None and body.spent == 10


def test_with_budget():
    status = BudgetStatus(FOOD, Money(100), Money(60), Money(40), 60, Money(120), date(2026, 9, 20))
    assert BudgetStatusBody.of(status).model_dump(mode="json")["over_on"] == "2026-09-20"
