from __future__ import annotations

import asyncio
import json

import pytest

from tests.ui.infrastructure.api.conftest import STATUS, client, recorder
from ui.application.dto import Period
from ui.application.errors import LedgerUnavailable
from ui.application.ports import BudgetGateway
from ui.application.values import CategoryId, IdempotencyKey, Money
from ui.infrastructure.api import HttpBudgetGateway


def gateway(body: object, status: int = 200):
    handler, seen = recorder(status, body)
    return HttpBudgetGateway(client(handler)), seen


def test_fills_the_port_and_lists_statuses():
    port: BudgetGateway
    port, seen = gateway([STATUS])
    statuses = asyncio.run(port.statuses(Period(2026, 9)))
    assert statuses[0].percent == 60 and seen[0].url.params["period"] == "2026-09"


def test_one_status_or_unavailable():
    port, seen = gateway([STATUS])
    assert asyncio.run(port.status(CategoryId("food"), Period(2026, 9))).limit == Money(300000)
    assert seen[0].url.params["category_id"] == "food"
    port, _ = gateway([])
    with pytest.raises(LedgerUnavailable):
        asyncio.run(port.status(CategoryId("salary"), Period(2026, 9)))


def test_set_limit_is_confirmed_and_null_clears():
    port, seen = gateway(STATUS)
    asyncio.run(port.set_limit(CategoryId("food"), None, IdempotencyKey("k1")))
    request = seen[0]
    assert request.method == "PUT" and request.url.path == "/v1/budgets/food"
    assert (
        request.headers["X-Confirmed-By"] == "user" and request.headers["Idempotency-Key"] == "k1"
    )
    assert json.loads(request.content) == {"limit_amount": None}
