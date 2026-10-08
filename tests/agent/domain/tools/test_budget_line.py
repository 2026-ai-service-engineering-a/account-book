from __future__ import annotations

from agent.domain.tools import BudgetLine
from agent.domain.values import Amount, CategoryId


def test_no_budget_means_nothing_below_spent():
    line = BudgetLine(CategoryId("cafe"), "카페", Amount(6_300), None, None, None, None, None)
    assert line.limit is None and line.over_on is None
