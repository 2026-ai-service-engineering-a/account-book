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
