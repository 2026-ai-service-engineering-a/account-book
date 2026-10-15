from __future__ import annotations

from api.interfaces.schemas import RunBody
from tests.api.application.use_cases.test_decide_run import proposed


def test_a_run_as_json_with_its_confirmations():
    run = proposed().runs.get("r1")
    assert run is not None
    body = RunBody.of(run).model_dump(mode="json")
    assert body["status"] == "awaiting_confirmation"
    assert body["tool_calls"][0]["confirmed_at"] is None


def test_carries_the_model_and_its_cost_for_the_audit_page():
    run = proposed().runs.get("r1")
    assert run is not None
    body = RunBody.of(run).model_dump(mode="json")
    assert (body["model"], body["steps"], body["tokens"], body["cost_usd"]) == (
        "gemini/flash",
        2,
        120,
        "0.000150",
    )
