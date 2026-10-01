from __future__ import annotations

import uuid

from tests.api.interfaces.routers.test_reports_router import client


def write(body: dict[str, object], confirmed: bool = True):
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    if confirmed:
        headers["X-Confirmed-By"] = "user"
    return client().put("/v1/budgets/cafe", json=body, headers=headers)


def test_status_lists_every_expense_category():
    body = client().get("/v1/budgets/status?period=2026-09").json()
    assert [s["category"]["id"] for s in body] == ["food", "cafe"]
    assert body[0]["limit"] == 300000 and body[1]["limit"] is None


def test_one_category():
    body = client().get("/v1/budgets/status?period=2026-09&category_id=cafe").json()
    assert len(body) == 1 and body[0]["spent"] == 5000


def test_set_and_clear():
    assert write({"limit_amount": 50000}).json()["limit"] == 50000
    assert write({"limit_amount": None}).json()["limit"] is None


def test_needs_confirmation_and_a_positive_amount():
    assert write({"limit_amount": 1}, confirmed=False).status_code == 412
    response = write({"limit_amount": 0})
    assert response.status_code == 422
    assert response.json()["error"]["details"] == {"amount": "예산은 0보다 커야 합니다."}
