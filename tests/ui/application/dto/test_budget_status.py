from __future__ import annotations

from ui.application.dto import BudgetStatus, Category, Direction
from ui.application.values import CategoryId, Money

FOOD = Category(CategoryId("food"), "식비", Direction.EXPENSE)


def test_over_only_when_spent_exceeds_limit():
    assert BudgetStatus(FOOD, Money(300_000), Money(300_001), Money(-1), 100, None, None).is_over
    assert not BudgetStatus(FOOD, Money(300_000), Money(300_000), Money(0), 100, None, None).is_over


def test_no_budget_is_never_over():
    assert not BudgetStatus(FOOD, None, Money(999_999), None, None, None, None).is_over
