from __future__ import annotations

import asyncio

import pytest

from tests.ui.conftest import draft, key
from ui.application.dto import Period
from ui.application.errors import LedgerValidationError
from ui.application.values import CategoryId, Money
from ui.infrastructure.memory import MemoryBudgetGateway, MemoryTransactionGateway

FOOD = CategoryId("food")


def test_status_without_budget_is_not_a_warning(store, clock):
    asyncio.run(
        MemoryTransactionGateway(store).create(draft(amount=31_000, category="cafe"), key("k"))
    )
    status = asyncio.run(
        MemoryBudgetGateway(store, clock).status(CategoryId("cafe"), Period(2026, 9))
    )
    assert (status.limit, status.spent, status.percent, status.is_over) == (
        None,
        Money(31_000),
        None,
        False,
    )


def test_over_budget_goes_negative(store, clock):
    asyncio.run(
        MemoryTransactionGateway(store).create(draft(amount=318_000, category="living"), key("k"))
    )
    budgets = MemoryBudgetGateway(store, clock)
    status = asyncio.run(budgets.set_limit(CategoryId("living"), Money(250_000), key("b1")))
    assert (status.remaining, status.percent, status.is_over) == (Money(-68_000), 127, True)


def test_clearing_and_rejecting_limits(store, clock):
    budgets = MemoryBudgetGateway(store, clock)
    asyncio.run(budgets.set_limit(FOOD, Money(300_000), key("b1")))
    assert asyncio.run(budgets.set_limit(FOOD, None, key("b2"))).limit is None
    with pytest.raises(LedgerValidationError):
        asyncio.run(budgets.set_limit(FOOD, Money(0), key("b3")))
    with pytest.raises(LedgerValidationError):
        asyncio.run(budgets.set_limit(CategoryId("salary"), Money(1_000), key("b4")))
