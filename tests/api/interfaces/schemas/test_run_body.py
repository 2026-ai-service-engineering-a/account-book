from __future__ import annotations

from api.interfaces.schemas import RunBody
from tests.api.application.use_cases.test_decide_run import proposed


def test_a_run_as_json_with_its_confirmations():
    run = proposed().runs.get("r1")
    assert run is not None
    body = RunBody.of(run).model_dump(mode="json")
    assert body["status"] == "awaiting_confirmation"
    assert body["tool_calls"][0]["confirmed_at"] is None
