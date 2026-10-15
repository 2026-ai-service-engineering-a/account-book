from __future__ import annotations

from agent.application.dto import RunSeat
from agent.application.errors import LedgerUnavailable, ModelUnavailable
from tests.agent.conftest import (
    SENTENCE,
    FakeLedger,
    FakeModel,
    FakeRecorder,
    extraction,
    search,
)
from tests.agent.interfaces.conftest import client_with

BODY = {"text": SENTENCE, "now": "2026-10-01T09:00:00+00:00", "timezone": "Asia/Seoul"}


def test_reads_with_the_users_reference_time_and_picks_a_category():
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    response = client_with(FakeModel(extraction()), ledger).post("/capture", json=BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == 5000 and body["merchant"] == "카페"
    assert body["occurred_at"] == "2026-10-01T15:00:00+09:00"
    assert body["category"]["category_id"] == "cafe" and body["category"]["strategy"] == "vector"


def test_api_down_still_fills_the_values():
    # 카테고리를 못 골라도 읽은 값은 살린다
    ledger = FakeLedger(LedgerUnavailable("ConnectError"))
    body = client_with(FakeModel(extraction()), ledger).post("/capture", json=BODY).json()
    assert body["amount"] == 5000 and body["category"]["category_id"] is None


def test_refusal_is_still_200():
    # 못 읽은 것은 실패가 아니라 답이다. ui가 말풍선으로 옮긴다
    response = client_with(FakeModel(extraction(kind="question"))).post("/capture", json=BODY)
    assert response.status_code == 200 and response.json()["refusal"]


def test_unavailable_model_is_503_with_a_code():
    response = client_with(FakeModel(ModelUnavailable("x"))).post("/capture", json=BODY)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


def test_bad_body_is_422():
    response = client_with(FakeModel()).post("/capture", json=BODY | {"timezone": "Nowhere"})
    assert response.status_code == 422


def test_leaves_the_run_with_the_category_pick():
    recorder = FakeRecorder()
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    client_with(FakeModel(extraction()), ledger, recorder).post("/capture", json=BODY)
    ((run, model),) = recorder.runs
    assert (run.seat, run.utterance, run.stop_reason, model) == (
        RunSeat.CAPTURE,
        SENTENCE,
        "read",
        "fake/model",
    )
    assert [c.tool for c in run.tool_calls] == ["suggest_category"]


def test_a_503_is_left_as_a_failed_run():
    recorder = FakeRecorder()
    client_with(FakeModel(ModelUnavailable("x")), recorder=recorder).post("/capture", json=BODY)
    ((run, _),) = recorder.runs
    assert run.failed and run.stop_reason == "model_unavailable"


def test_the_answer_goes_out_even_when_recording_fails():
    recorder = FakeRecorder(fail=LedgerUnavailable("ConnectError"))
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    response = client_with(FakeModel(extraction()), ledger, recorder).post("/capture", json=BODY)
    assert response.status_code == 200 and response.json()["amount"] == 5000
