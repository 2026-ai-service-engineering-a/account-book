from __future__ import annotations

from tests.agent.conftest import FakeModel
from tests.agent.interfaces.conftest import client_with


def test_headless_no_docs_pages():
    client = client_with(FakeModel())
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
