from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

import httpx
import pytest

from agent.application.errors import LedgerUnavailable
from agent.infrastructure.http import HttpInsightCache

KEY = "c" * 64


def cache(handler: Callable[[httpx.Request], httpx.Response]) -> HttpInsightCache:
    return HttpInsightCache("http://api:8000", timeout=1, transport=httpx.MockTransport(handler))


def test_get_reads_a_hit_and_a_miss():
    replies = iter([{"key": KEY, "body": {"highlights": ["a"]}}, {"key": KEY, "body": None}])

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/v1/insights/cache/{KEY}"
        return httpx.Response(200, json=next(replies))

    adapter = cache(handler)
    assert asyncio.run(adapter.get(KEY)) == {"highlights": ["a"]}
    assert asyncio.run(adapter.get(KEY)) is None


def test_put_sends_the_body_with_a_key_that_follows_the_body():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(204)

    adapter = cache(handler)
    asyncio.run(adapter.put(KEY, {"highlights": ["a"]}))
    asyncio.run(adapter.put(KEY, {"highlights": ["b"]}))
    assert json.loads(seen[0].content) == {"body": {"highlights": ["a"]}}
    first, second = (r.headers["Idempotency-Key"] for r in seen)
    assert first.startswith("insight:") and first != second  # 다른 답은 새 요청이다


def test_an_unreachable_api_is_unavailable():
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LedgerUnavailable):
        asyncio.run(cache(down).get(KEY))
