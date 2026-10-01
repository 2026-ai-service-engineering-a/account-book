from __future__ import annotations

from fastapi.testclient import TestClient

from agent.main import create_app
from tests.agent.conftest import FakeLedger, FakeModel


def client_with(model: FakeModel, ledger: FakeLedger | None = None) -> TestClient:
    return TestClient(create_app(model=model, ledger=ledger or FakeLedger()))
