from __future__ import annotations

import asyncio
import json

import pytest

from tests.ui.conftest import draft
from tests.ui.infrastructure.api.conftest import TX, client, recorder
from ui.application.dto import Direction, Period, TransactionFilter
from ui.application.errors import LedgerUnavailable
from ui.application.ports import TransactionGateway
from ui.application.values import CategoryId, IdempotencyKey, PageCursor, RunId, TransactionId
from ui.infrastructure.api import HttpTransactionGateway


def gateway(status: int = 200, body: object = None):
    handler, seen = recorder(status, body)
    return HttpTransactionGateway(client(handler)), seen


def test_fills_the_port():
    port: TransactionGateway = gateway()[0]
    assert port is not None


def test_search_sends_the_filter_as_query():
    port, seen = gateway(body={"items": [TX], "next_cursor": "c2"})
    criteria = TransactionFilter(Period(2026, 9), Direction.EXPENSE, CategoryId("food"), "김밥")
    page = asyncio.run(port.search(criteria, PageCursor("c1"), limit=20))
    assert dict(seen[0].url.params) == {
        "period": "2026-09",
        "limit": "20",
        "direction": "expense",
        "category_id": "food",
        "q": "김밥",
        "cursor": "c1",
    }
    assert page.items[0].merchant == "김밥천국" and page.next_cursor == "c2"


def test_exists_any_asks_for_one():
    port, seen = gateway(body={"items": [], "next_cursor": None})
    assert asyncio.run(port.exists_any()) is False and seen[0].url.params["limit"] == "1"


def test_create_is_confirmed_by_the_user_and_carries_the_key_and_run():
    port, seen = gateway(201, TX)
    asyncio.run(port.create(draft(), IdempotencyKey("k1"), RunId("run-1")))
    request = seen[0]
    assert request.method == "POST" and request.headers["Idempotency-Key"] == "k1"
    assert (
        request.headers["X-Confirmed-By"] == "user" and request.headers["X-Agent-Run-Id"] == "run-1"
    )
    body = json.loads(request.content)
    assert body["amount"] == 8500 and body["occurred_at"].endswith("+09:00")


def test_update_and_delete_paths():
    port, seen = gateway(200, TX)
    asyncio.run(port.update(TransactionId("t1"), draft(), IdempotencyKey("k2")))
    assert seen[0].method == "PATCH" and seen[0].url.path == "/v1/transactions/t1"
    port, seen = gateway(204)
    asyncio.run(port.delete(TransactionId("t1"), IdempotencyKey("k3")))
    assert seen[0].method == "DELETE" and seen[0].headers["X-Confirmed-By"] == "user"


def test_strange_body_is_unavailable():
    port, _ = gateway(body={"items": "nope"})
    with pytest.raises(LedgerUnavailable):
        asyncio.run(port.exists_any())
