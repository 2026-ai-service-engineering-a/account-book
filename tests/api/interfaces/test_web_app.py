from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from tests.api.conftest import FixedProbe


def test_headless_no_docs_pages():
    client = TestClient(create_app(database=FixedProbe()))
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
