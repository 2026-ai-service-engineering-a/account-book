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


FOOD = {"id": "food", "name": "식비", "direction": "expense"}
MONTHLY = {
    "period": "2026-09",
    "totals": {"expense": 185000, "income": 3000000},
    "previous": {"expense": 34000, "income": 0},
    "by_category": [
        {
            "category": FOOD,
            "this_month": 180000,
            "last_month": 30000,
            "delta": 150000,
            "percent": 500,
        }
    ],
    "months": [
        {"period": "2026-08", "expense": 34000, "income": 0},
        {"period": "2026-09", "expense": 185000, "income": 3000000},
    ],
    "through_day": 3,
}
STATUS = {
    "category": FOOD,
    "limit": 300000,
    "spent": 180000,
    "remaining": 120000,
    "percent": 60,
    "projected": 1800000,
    "over_on": "2026-09-06",
}
PACE = {
    "category": FOOD,
    "limit": 300000,
    "cumulative": [100000, 180000, 180000],
    "days_in_month": 30,
    "projected": 1800000,
    "over_on": "2026-09-06",
}
