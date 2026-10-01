from __future__ import annotations

from collections.abc import Callable

import httpx

from ui.infrastructure.api import ApiClient

TX = {
    "id": "t1",
    "direction": "expense",
    "amount": 8500,
    "occurred_at": "2026-09-16T03:30:00+00:00",
    "category_id": "food",
    "account_id": "card",
    "merchant": "김밥천국",
    "memo": "",
    "source": "agent",
    "run_id": "run-1",
}


def client(handler: Callable[[httpx.Request], httpx.Response]) -> ApiClient:
    return ApiClient("http://api:8000", timeout=1, transport=httpx.MockTransport(handler))


def recorder(status: int = 200, body: object = None):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if status == 204:
            return httpx.Response(204)
        return httpx.Response(status, json=body)

    return handler, seen
