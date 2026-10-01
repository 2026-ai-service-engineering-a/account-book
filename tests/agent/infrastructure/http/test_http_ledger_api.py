from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from agent.application.dto import CategoryQuery
from agent.application.errors import LedgerUnavailable
from agent.domain.values import Direction
from agent.infrastructure.http import HttpLedgerApi
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
