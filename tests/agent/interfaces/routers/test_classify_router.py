from __future__ import annotations

from agent.application.errors import LedgerUnavailable, ModelUnavailable
from tests.agent.conftest import FakeLedger, FakeModel, evidence, search
from tests.agent.interfaces.conftest import client_with

BODY = {"merchant": "쿠팡이츠", "memo": "", "direction": "expense"}


def test_returns_the_choice():
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    body = client_with(FakeModel(), ledger).post("/classify", json=BODY).json()
    assert body["category_id"] == "cafe" and body["strategy"] == "vector"


def test_ledger_down_is_503_with_a_code():
    response = client_with(FakeModel(), FakeLedger(LedgerUnavailable("x"))).post(
        "/classify", json=BODY
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ledger_unavailable"


def test_model_down_is_503():
    ambiguous = search(
        candidates=(("living", 0.6), ("food", 0.4)), found=(evidence("t9", "쿠팡", "living"),)
    )
    response = client_with(FakeModel(ModelUnavailable("x")), FakeLedger(ambiguous)).post(
        "/classify", json=BODY
    )
    assert response.status_code == 503 and response.json()["error"]["code"] == "model_unavailable"
