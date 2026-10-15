from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

import httpx

from agent.infrastructure.http import HttpProposalBook
from tests.agent.infrastructure.http.test_proposal_reply import RUN


def book(handler: Callable[[httpx.Request], httpx.Response]) -> HttpProposalBook:
    return HttpProposalBook("http://api:8000", timeout=1, transport=httpx.MockTransport(handler))


def test_a_missing_run_is_none():
    assert asyncio.run(book(lambda r: httpx.Response(404, json={})).get("nope")) is None


def test_decisions_are_writes_with_their_own_keys():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=RUN)

    adapter = book(handler)
    asyncio.run(adapter.confirm("r1", "c2"))
    asyncio.run(adapter.close("r1", "done", "confirmed", {"c2": {"transaction_id": "t1"}}))
    confirm, close = seen
    assert confirm.url.path == "/v1/runs/r1/confirm" and json.loads(confirm.content) == {
        "call_id": "c2"
    }
    assert confirm.headers["Idempotency-Key"] == "run:r1:confirm"
    assert json.loads(close.content)["results"] == [
        {"call_id": "c2", "result": {"transaction_id": "t1"}}
    ]
    assert close.headers["Idempotency-Key"] == "run:r1:close:confirmed"
