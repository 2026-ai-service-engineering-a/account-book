from __future__ import annotations

from api.interfaces.schemas import TransactionBody
from tests.api.application.use_cases.test_create_transaction import CREATE
from tests.api.conftest import FakeUnitOfWork, draft


def test_plain_values_on_the_wire():
    created = CREATE(FakeUnitOfWork(), draft(), run_id="run-1", confirmed=False)
    body = TransactionBody.of(created).model_dump(mode="json")
    assert body["amount"] == 8500 and body["source"] == "agent" and body["run_id"] == "run-1"
    assert body["occurred_at"] == "2026-09-16T12:30:00+09:00"
