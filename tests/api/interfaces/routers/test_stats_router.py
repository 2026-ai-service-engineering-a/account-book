from __future__ import annotations

from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import client_with

SEPTEMBER = {"from": "2026-09-01T00:00:00+09:00", "to": "2026-10-01T00:00:00+09:00"}
AUGUST = {"from": "2026-08-01T00:00:00+09:00", "to": "2026-09-01T00:00:00+09:00"}


def test_frequency_with_the_summary_filters():
    client = client_with(ledger())
    assert client.get("/v1/stats/frequency", params=SEPTEMBER).json() == {
        "count": 3,
        "day_count": 3,
        "avg_gap_days": 1.0,
        "avg_amount": 61667,
    }
    cafe = client.get("/v1/stats/frequency", params={**SEPTEMBER, "category_id": "cafe"})
    assert cafe.json()["count"] == 1
    income = client.get("/v1/stats/frequency", params={**SEPTEMBER, "direction": "income"})
    assert income.json()["avg_amount"] == 3_000_000


def test_compare_by_category():
    params = {
        "a_from": AUGUST["from"],
        "a_to": AUGUST["to"],
        "b_from": SEPTEMBER["from"],
        "b_to": SEPTEMBER["to"],
    }
    body = client_with(ledger()).get("/v1/stats/compare", params=params).json()
    assert [(r["category"]["id"], r["a"], r["b"], r["delta"], r["percent"]) for r in body] == [
        ("food", 30000, 180000, 150000, 500),
        ("cafe", 4000, 5000, 1000, 25),
    ]


def test_naive_times_are_422():
    response = client_with().get(
        "/v1/stats/frequency", params={"from": "2026-09-01T00:00:00", "to": SEPTEMBER["to"]}
    )
    assert response.status_code == 422
    assert "from" in response.json()["error"]["details"]


def test_backwards_range_is_422_on_the_end():
    params = {"from": SEPTEMBER["to"], "to": SEPTEMBER["from"]}
    response = client_with().get("/v1/stats/frequency", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert set(response.json()["error"]["details"]) == {"to"}


def test_period_names_are_not_accepted():
    response = client_with().get("/v1/stats/frequency", params={"period": "last_week"})
    assert response.status_code == 422
