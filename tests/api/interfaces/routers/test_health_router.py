from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from tests.api.conftest import FixedProbe


def test_ok_when_the_database_answers():
    response = TestClient(create_app(database=FixedProbe(up=True))).get("/v1/healthz")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


def test_503_with_a_code_when_it_does_not():
    response = TestClient(create_app(database=FixedProbe(up=False))).get("/v1/healthz")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "db_unavailable"
