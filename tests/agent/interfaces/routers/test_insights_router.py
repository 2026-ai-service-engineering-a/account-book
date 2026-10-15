from __future__ import annotations

from agent.application.dto import RunSeat
from agent.application.errors import ModelUnavailable
from tests.agent.application.use_cases.test_build_insights import (
    OUTLIERS,
    SAID,
    assembled,
    chart,
    ledger,
    plan,
)
from tests.agent.conftest import FakeModel, FakeRecorder
from tests.agent.interfaces.conftest import client_with

BODY = {"month": "2026-09", "now": "2026-10-15T09:00:00+09:00", "timezone": "Asia/Seoul"}


def test_charts_with_values_and_sentences_and_the_run_is_left():
    recorder = FakeRecorder()
    model = FakeModel(plan(OUTLIERS), assembled([chart()], SAID))
    response = client_with(model, ledger(), recorder).post("/insights", json=BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["highlights"] == [SAID]
    assert body["charts"][0]["points"][1] == {"label": "생활", "value": 1050000, "annotated": True}
    ((run, _),) = recorder.runs
    assert (run.seat, run.seat.flow, run.utterance, run.stop_reason, run.steps) == (
        RunSeat.INSIGHT,
        "plan_execute",
        "2026-09",
        "assembled",
        2,
    )
    planned = run.tool_calls[2]
    assert planned.tool == "detect_outliers" and planned.result is not None
    assert planned.result["why"] == "detect_outliers를 보려고"
    assert "why" not in (run.tool_calls[0].result or {})  # 고정 호출에는 이유가 없다


def test_a_quiet_month_is_200_and_empty():
    model = FakeModel(plan(), assembled([]))
    response = client_with(model, ledger()).post("/insights", json=BODY)
    assert response.status_code == 200 and response.json() == {"charts": [], "highlights": []}


def test_an_unreachable_model_is_503_and_left_as_failed():
    recorder = FakeRecorder()
    response = client_with(FakeModel(ModelUnavailable("x")), ledger(), recorder).post(
        "/insights", json=BODY
    )
    assert response.status_code == 503
    assert recorder.runs[0][0].failed and recorder.runs[0][0].stop_reason == "model_unavailable"


def test_a_month_not_yet_come_is_422():
    late = BODY | {"month": "2026-11"}
    assert client_with(FakeModel(), ledger()).post("/insights", json=late).status_code == 422


def test_a_cached_answer_is_left_as_a_run_without_model_calls():
    recorder = FakeRecorder()
    client = client_with(FakeModel(plan(OUTLIERS), assembled([chart()], SAID)), ledger(), recorder)
    first = client.post("/insights", json=BODY).json()
    again = client.post("/insights", json=BODY).json()  # 같은 앱 — 같은 캐시
    assert again == first
    run = recorder.runs[1][0]
    assert (run.stop_reason, run.steps, run.tool_calls) == ("cached", 0, ())
