from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.infrastructure.settings import Settings
from api.main import create_app
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL, FixedClock, FixedProbe

CLOCK = FixedClock(datetime(2026, 9, 3, 18, tzinfo=SEOUL))


def client() -> TestClient:
    settings = Settings(_env_file=None, postgres_password=SecretStr("unused"))
    app = create_app(settings, database=FixedProbe(), unit_of_work=ledger(), clock=CLOCK)
    return TestClient(app)


def test_summary_uses_the_list_filters():
    assert client().get("/v1/summary?period=2026-09").json() == {
        "expense": 185000,
        "income": 3000000,
    }
    assert client().get("/v1/summary?period=2026-09&category_id=cafe").json()["expense"] == 5000


def test_monthly_report():
    body = client().get("/v1/reports/monthly?period=2026-09").json()
    assert body["previous"]["expense"] == 34000 and body["through_day"] == 3
    assert body["by_category"][0]["category"]["id"] == "food"


def test_pace_or_null():
    assert (
        client().get("/v1/reports/pace?category_id=food&period=2026-09").json()["over_on"]
        == "2026-09-06"
    )
    assert client().get("/v1/reports/pace?category_id=cafe&period=2026-09").json() is None


def test_bad_period_is_422():
    assert client().get("/v1/reports/monthly?period=2026-9").status_code == 422


def test_summary_takes_a_range_instead_of_a_month():
    two_days = {"from": "2026-09-01T00:00:00+09:00", "to": "2026-09-03T00:00:00+09:00"}
    assert client().get("/v1/summary", params=two_days).json()["expense"] == 180000


def test_summary_refuses_month_and_range_together():
    two_days = {"from": "2026-09-01T00:00:00+09:00", "to": "2026-09-03T00:00:00+09:00"}
    params = {"period": "2026-09", **two_days}
    response = client().get("/v1/summary", params=params)
    assert response.status_code == 422
    assert set(response.json()["error"]["details"]) == {"period"}
