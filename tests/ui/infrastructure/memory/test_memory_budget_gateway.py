from __future__ import annotations

import asyncio

import pytest

from tests.ui.conftest import draft
from ui.application.dto import Period
from ui.application.errors import LedgerValidationError
from ui.infrastructure.memory import MemoryBudgetGateway, MemoryTransactionGateway


def test_status_without_budget_is_not_a_warning(store, clock):
    asyncio.run(MemoryTransactionGateway(store).create(draft(amount=31_000, category="cafe"), "k"))
    status = asyncio.run(MemoryBudgetGateway(store, clock).status("cafe", Period(2026, 9)))
    assert (status.limit, status.spent, status.percent, status.is_over) == (
        None,
        31_000,
        None,
        False,
    )


def test_over_budget_goes_negative(store, clock):
    asyncio.run(
        MemoryTransactionGateway(store).create(draft(amount=318_000, category="living"), "k")
    )
    budgets = MemoryBudgetGateway(store, clock)
    status = asyncio.run(budgets.set_limit("living", 250_000, "b1"))
    assert (status.remaining, status.percent, status.is_over) == (-68_000, 127, True)


def test_clearing_and_rejecting_limits(store, clock):
    budgets = MemoryBudgetGateway(store, clock)
    asyncio.run(budgets.set_limit("food", 300_000, "b1"))
    assert asyncio.run(budgets.set_limit("food", None, "b2")).limit is None
    with pytest.raises(LedgerValidationError):
        asyncio.run(budgets.set_limit("food", 0, "b3"))
    with pytest.raises(LedgerValidationError):
        asyncio.run(budgets.set_limit("salary", 1_000, "b4"))
