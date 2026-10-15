from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.interfaces.schemas import RunDecision


def test_results_by_call_id_and_only_done_or_aborted():
    decision = RunDecision(status="done", results=[{"call_id": "c2", "result": {"id": "t1"}}])
    assert decision.result_map() == {"c2": {"id": "t1"}}
    with pytest.raises(ValidationError):
        RunDecision.model_validate({"status": "awaiting_confirmation"})
