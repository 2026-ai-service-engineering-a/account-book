from __future__ import annotations

import asyncio
import json
from datetime import date, datetime

import httpx
import pytest

from agent.application.dto import CategoryQuery, TransactionFilter
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.domain.values import CategoryId, Direction, TimeRange
from agent.infrastructure.http import HttpLedgerApi
from tests.agent.conftest import SEOUL
from tests.agent.infrastructure.http.test_suggest_reply import BODY


def api(handler) -> HttpLedgerApi:
    return HttpLedgerApi("http://ui:8080", timeout=1, transport=httpx.MockTransport(handler))


def recorder(status: int = 200, body: object = BODY):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=body)

    return handler, seen


def test_suggest_posts_the_query():
    handler, seen = recorder()
    query = CategoryQuery("블루보틀", "", Direction.EXPENSE, "m@768", (0.1, 0.2))
    result = asyncio.run(api(handler).suggest(query))
    assert seen[0].url == "http://ui:8080/v1/categories/suggest"
    assert json.loads(seen[0].content) == {
        "merchant": "블루보틀",
        "memo": "",
        "direction": "expense",
        "embedding_model": "m@768",
        "query_vector": [0.1, 0.2],
    }
    assert result.candidates[0].category_id == "cafe"


def test_pending_asks_for_the_model():
    handler, seen = recorder(body={"items": [{"text_hash": "h", "text": "t"}]})
    items = asyncio.run(api(handler).pending("m@768", 100))
    assert seen[0].url.params["model"] == "m@768" and items[0].text == "t"


def test_put_embedding_sends_a_stable_idempotency_key():
    handler, seen = recorder(204, None)
    asyncio.run(api(handler).put_embedding("h1", "m@768", (0.5,)))
    assert seen[0].method == "PUT" and seen[0].url.path == "/v1/embeddings/h1"
    assert seen[0].headers["Idempotency-Key"] == "emb:m@768:h1"


@pytest.mark.parametrize(("status", "body"), [(503, {"error": {}}), (200, {"strategy": "?"})])
def test_errors_and_strange_bodies_are_unavailable(status, body):
    handler, _ = recorder(status, body)
    with pytest.raises(LedgerUnavailable):
        asyncio.run(api(handler).suggest(CategoryQuery("x", "", Direction.EXPENSE)))


def test_connection_refused_is_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(LedgerUnavailable, match="ConnectError"):
        asyncio.run(api(handler).pending("m", 1))


WEEK = TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL))
FREQUENCY = {"count": 3, "day_count": 3, "avg_gap_days": 1.0, "avg_amount": 5267}


def test_filter_becomes_query_with_offsets_encoded():
    handler, seen = recorder(body=FREQUENCY)
    where = TransactionFilter(WEEK, CategoryId("cafe"), "스타", Direction.EXPENSE)
    found = asyncio.run(api(handler).frequency(where))
    assert seen[0].url.path == "/v1/stats/frequency"
    assert dict(seen[0].url.params) == {
        "from": "2026-09-28T00:00:00+09:00",
        "to": "2026-10-05T00:00:00+09:00",
        "category_id": "cafe",
        "q": "스타",
        "direction": "expense",
    }
    assert b"%2B09%3A00" in seen[0].url.raw_path  # 그대로 보내면 +가 공백이 된다
    assert found.day_count == 3


def test_empty_filters_are_left_out():
    handler, seen = recorder(body={"expense": 0, "income": 0})
    asyncio.run(api(handler).summary(TransactionFilter(WEEK)))
    assert set(seen[0].url.params) == {"from", "to"}


def test_transactions_compare_and_budgets_hit_their_endpoints():
    page: dict[str, object] = {"items": [], "next_cursor": None}
    handler, seen = recorder(body=page)
    asyncio.run(api(handler).transactions(TransactionFilter(WEEK), limit=20))
    assert seen[0].url.path == "/v1/transactions" and seen[0].url.params["limit"] == "20"
    handler, seen = recorder(body=[])
    asyncio.run(api(handler).compare(WEEK, WEEK, CategoryId("cafe")))
    assert set(seen[0].url.params) == {"a_from", "a_to", "b_from", "b_to", "category_id"}
    handler, seen = recorder(body=[])
    asyncio.run(api(handler).budget_status(date(2026, 8, 1), None))
    assert dict(seen[0].url.params) == {"period": "2026-08"}


@pytest.mark.parametrize(
    ("status", "body", "code", "details"),
    [
        (422, {"error": {"code": "validation_error", "message": "x", "details": {"to": "끝"}}},
         "validation_error", {"to": "끝"}),
        (404, {"error": {"code": "not_found", "message": "x"}}, "not_found", {}),
    ],
)  # fmt: skip
def test_client_errors_are_rejections_with_the_code(status, body, code, details):
    handler, _ = recorder(status, body)
    with pytest.raises(LedgerRejected) as error:
        asyncio.run(api(handler).summary(TransactionFilter(WEEK)))
    assert (error.value.status, error.value.code, error.value.details) == (status, code, details)


@pytest.mark.parametrize(
    ("status", "body"), [(500, {"error": {"code": "internal_error"}}), (400, "?")]
)
def test_server_errors_and_unreadable_4xx_are_not_rejections(status, body):
    handler, _ = recorder(status, body)
    with pytest.raises(LedgerUnavailable) as error:
        asyncio.run(api(handler).summary(TransactionFilter(WEEK)))
    assert not isinstance(error.value, LedgerRejected)


def test_categories_are_the_whole_dictionary():
    handler, seen = recorder(body=[{"id": "salary", "name": "급여", "direction": "income"}])
    (line,) = asyncio.run(api(handler).categories())
    assert seen[0].url.path == "/v1/categories" and not seen[0].url.params
    assert line.id == "salary"
