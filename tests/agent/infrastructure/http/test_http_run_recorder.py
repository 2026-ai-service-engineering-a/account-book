from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from agent.application.dto import RunRecord, RunSeat, ToolCallRecord
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.infrastructure.http import HttpRunRecorder

CALL = ToolCallRecord("c1", "suggest_category", {"merchant": "블루보틀"}, {"category_id": "cafe"})
RUN = RunRecord("r-1", RunSeat.CLASSIFY, "블루보틀", "history", tool_calls=(CALL,))


def recorder(status: int = 201, body: object | None = None):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=body if body is not None else {"id": "r-1"})

    adapter = HttpRunRecorder("http://api:8000", timeout=1, transport=httpx.MockTransport(handler))
    return adapter, seen


def test_posts_the_run_with_its_own_key():
    adapter, seen = recorder()
    asyncio.run(adapter.record(RUN, "gemini/flash"))
    (request,) = seen
    assert request.url == "http://api:8000/v1/runs"
    assert request.headers["Idempotency-Key"] == "run:r-1"
    assert json.loads(request.content) == {
        "id": "r-1",
        "seat": "classify",
        "flow": "single",
        "utterance": "블루보틀",
        "model": "gemini/flash",
        "steps": 0,
        "tokens": 0,
        "cost_usd": 0.0,
        "status": "done",
        "stop_reason": "history",
        "tool_calls": [
            {
                "call_id": "c1",
                "tool": "suggest_category",
                "args": {"merchant": "블루보틀"},
                "result": {"category_id": "cafe"},
            }
        ],
    }


def test_a_failed_run_says_so():
    adapter, seen = recorder()
    run = RunRecord("r-2", RunSeat.CHAT, "질문", "internal_error", failed=True)
    asyncio.run(adapter.record(run, "m"))
    body = json.loads(seen[0].content)
    assert (body["status"], body["flow"]) == ("failed", "react")


def test_a_refusal_carries_the_code():
    adapter, _ = recorder(422, {"error": {"code": "validation_error", "message": "x"}})
    with pytest.raises(LedgerRejected) as error:
        asyncio.run(adapter.record(RUN, "m"))
    assert error.value.code == "validation_error"


def test_server_errors_and_unreachable_api_are_unavailable():
    adapter, _ = recorder(500, {"error": {"code": "internal_error"}})
    with pytest.raises(LedgerUnavailable):
        asyncio.run(adapter.record(RUN, "m"))

    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    unreachable = HttpRunRecorder("http://api:8000", timeout=1, transport=httpx.MockTransport(down))
    with pytest.raises(LedgerUnavailable, match="ConnectError"):
        asyncio.run(unreachable.record(RUN, "m"))
