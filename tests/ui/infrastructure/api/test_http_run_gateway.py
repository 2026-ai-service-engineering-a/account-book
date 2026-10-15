from __future__ import annotations

import asyncio

import httpx
import pytest

from tests.ui.infrastructure.api.test_run_detail_reply import CALL
from tests.ui.infrastructure.api.test_run_line_reply import LINE
from ui.application.dto import RunFilter
from ui.application.errors import LedgerUnavailable
from ui.application.values import PageCursor, RunId
from ui.infrastructure.api import ApiClient, HttpRunGateway


def gateway(handler) -> HttpRunGateway:
    return HttpRunGateway(
        ApiClient("http://api", timeout=1, transport=httpx.MockTransport(handler))
    )


def test_asks_for_a_page_with_the_filter_and_only_reads():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"items": [LINE], "next_cursor": None})

    criteria = RunFilter(seat="mcp", status="done")
    page = asyncio.run(gateway(handler).page(criteria, PageCursor("abc")))
    assert page.items[0].client == "Claude"
    (request,) = seen
    assert request.method == "GET" and request.url.path == "/v1/runs"
    assert dict(request.url.params) == {
        "limit": "30",
        "seat": "mcp",
        "status": "done",
        "cursor": "abc",
    }


def test_a_missing_run_is_none_and_a_found_one_has_its_calls():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/nope"):
            return httpx.Response(404, json={"error": {"code": "not_found", "message": "없다"}})
        body = {k: v for k, v in LINE.items() if k != "tool_count"} | {"tool_calls": [CALL]}
        return httpx.Response(200, json=body)

    assert asyncio.run(gateway(handler).get(RunId("nope"))) is None
    found = asyncio.run(gateway(handler).get(RunId("r1")))
    assert found is not None and found.calls[0].tool == "summarize_spending"


def test_an_odd_shape_is_unavailable():
    with pytest.raises(LedgerUnavailable):
        asyncio.run(gateway(lambda r: httpx.Response(200, json={"rows": []})).page(RunFilter()))
