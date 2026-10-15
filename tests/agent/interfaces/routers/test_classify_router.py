from __future__ import annotations

from agent.application.errors import LedgerUnavailable, ModelUnavailable
from tests.agent.conftest import FakeLedger, FakeModel, FakeRecorder, evidence, search
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


def test_leaves_the_run_with_the_strategy_as_its_stop():
    recorder = FakeRecorder()
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    client_with(FakeModel(), ledger, recorder).post("/classify", json=BODY)
    ((run, _),) = recorder.runs
    assert run.utterance == "쿠팡이츠" and run.stop_reason == "vector"
    assert run.tool_calls[0].result is not None
    assert run.tool_calls[0].result["category_id"] == "cafe"


def test_a_503_is_left_and_a_failed_record_does_not_change_the_answer():
    recorder = FakeRecorder()
    down = FakeLedger(LedgerUnavailable("x"))
    client_with(FakeModel(), down, recorder).post("/classify", json=BODY)
    assert recorder.runs[0][0].stop_reason == "ledger_unavailable"
    broken = FakeRecorder(fail=RuntimeError("boom"))
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    response = client_with(FakeModel(), ledger, broken).post("/classify", json=BODY)
    assert response.status_code == 200 and response.json()["category_id"] == "cafe"
