from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from mcp_server.application.dto import RunEntry
from mcp_server.application.errors import LedgerUnavailable
from mcp_server.infrastructure.http import HttpRunLog

ANSWER = {"call_id": "r1", "ok": True, "data": {"expense": {"amount": 1, "currency": "KRW"}}}


def test_records_one_direct_mcp_run_with_the_clients_name():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"id": "r1"})

    log = HttpRunLog("http://api", timeout=1, transport=httpx.MockTransport(handler))
    asyncio.run(
        log.record(RunEntry("r1", "summarize_spending", {"period": "today"}, ANSWER, "Claude"))
    )
    (request,) = seen
    assert request.url.path == "/v1/runs" and request.headers["Idempotency-Key"] == "run:r1"
    body = json.loads(request.content)
    assert (body["seat"], body["flow"], body["client"], body["model"]) == (
        "mcp",
        "direct",
        "Claude",
        "external",
    )
    assert (body["status"], body["stop_reason"], body["tokens"]) == ("done", "answered", 0)
    assert body["tool_calls"] == [
        {
            "call_id": "r1",
            "tool": "summarize_spending",
            "args": {"period": "today"},
            "result": ANSWER,
        }
    ]


def test_an_unreachable_api_is_unavailable():
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    log = HttpRunLog("http://api", timeout=1, transport=httpx.MockTransport(refused))
    with pytest.raises(LedgerUnavailable):
        asyncio.run(log.record(RunEntry("r1", "summarize_spending", {}, ANSWER, "Claude")))
