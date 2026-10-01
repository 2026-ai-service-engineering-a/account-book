from __future__ import annotations

from fastapi.testclient import TestClient

from agent.main import create_app
from tests.agent.conftest import FakeModel


def client_with(model: FakeModel) -> TestClient:
    return TestClient(create_app(model=model))
