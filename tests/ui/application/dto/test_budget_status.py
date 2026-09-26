from __future__ import annotations

from ui.application.dto import BudgetStatus, Category, Direction

FOOD = Category("food", "식비", Direction.EXPENSE)


def test_over_only_when_spent_exceeds_limit():
    assert BudgetStatus(FOOD, 300_000, 300_001, -1, 100, None, None).is_over
    assert not BudgetStatus(FOOD, 300_000, 300_000, 0, 100, None, None).is_over


def test_no_budget_is_never_over():
    assert not BudgetStatus(FOOD, None, 999_999, None, None, None, None).is_over
