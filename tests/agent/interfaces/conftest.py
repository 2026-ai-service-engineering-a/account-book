from __future__ import annotations

from fastapi.testclient import TestClient

from agent.main import create_app
from tests.agent.conftest import FakeInsightCache, FakeLedger, FakeModel, FakeRecorder
from tests.agent.fake_audit import FakeAuditTable


def client_with(
    model: FakeModel,
    ledger: FakeLedger | None = None,
    recorder: FakeRecorder | FakeAuditTable | None = None,
    book: FakeAuditTable | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            model=model,
            ledger=ledger or FakeLedger(),
            recorder=recorder or FakeRecorder(),
            cache=FakeInsightCache(),
            book=book or FakeAuditTable(),
        )
    )
