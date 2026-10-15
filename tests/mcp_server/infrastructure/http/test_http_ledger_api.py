from __future__ import annotations

import asyncio
from datetime import date, datetime

import httpx
import pytest

from mcp_server.application.dto import LedgerFilter
from mcp_server.application.errors import LedgerRejected, LedgerUnavailable
from mcp_server.domain.values import Direction, TimeRange
from mcp_server.infrastructure.http import HttpLedgerApi
from tests.mcp_server.conftest import SEOUL

OCTOBER = TimeRange(datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 11, 1, tzinfo=SEOUL))


def api(handler) -> HttpLedgerApi:
    return HttpLedgerApi("http://api", timeout=1, transport=httpx.MockTransport(handler))


def test_sums_with_the_offset_kept_and_only_reads():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"expense": 412000, "income": 0})

    where = LedgerFilter(OCTOBER, "food", "카페", Direction.EXPENSE)
    row = asyncio.run(api(handler).summary(where))
    assert row["expense"] == {"amount": 412000, "currency": "KRW"}
    (request,) = seen
    assert request.method == "GET" and request.url.path == "/v1/summary"
    assert request.url.params["from"] == "2026-10-01T00:00:00+09:00"
    assert (request.url.params["q"], request.url.params["direction"]) == ("카페", "expense")


def test_the_budget_is_asked_by_month():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    assert asyncio.run(api(handler).budget_status(date(2026, 9, 1), "")) == []
    assert dict(seen[0].url.params) == {"period": "2026-09"}


def test_a_4xx_is_a_refusal_and_a_5xx_or_odd_shape_is_unavailable():
    refused = httpx.Response(404, json={"error": {"code": "not_found", "message": "없다"}})
    with pytest.raises(LedgerRejected):
        asyncio.run(api(lambda r: refused).compare(OCTOBER, OCTOBER, ""))
    for response in (httpx.Response(503), httpx.Response(200, json={"total": 1})):
        with pytest.raises(LedgerUnavailable):
            asyncio.run(api(lambda r, response=response: response).frequency(LedgerFilter(OCTOBER)))
