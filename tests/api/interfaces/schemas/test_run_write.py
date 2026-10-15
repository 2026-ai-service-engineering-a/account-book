from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from api.domain.values import RunSeat, RunStatus
from api.interfaces.schemas import RunWrite

RUN_ID = "0b6f0e4e-1c1e-4a51-9d2b-9a1f3c0d2e10"


def run_body(run_id: str = RUN_ID, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "id": run_id,
        "seat": "chat",
        "flow": "react",
        "utterance": "이번 달 카페에 얼마 썼어?",
        "model": "gemini/flash",
        "steps": 2,
        "tokens": 120,
        "cost_usd": "0.00015",
        "status": "done",
        "stop_reason": "answered",
        "tool_calls": [
            {"call_id": "c1", "tool": "summarize_spending", "args": {"q": "카페"}, "result": {}}
        ],
    }
    return body | overrides


def test_turns_into_a_record():
    record = RunWrite.model_validate(run_body()).record()
    assert record.seat is RunSeat.CHAT and record.status is RunStatus.DONE
    assert record.cost_usd == Decimal("0.00015") and record.tool_calls[0].call_id == "c1"


@pytest.mark.parametrize(
    "overrides",
    [
        {"seat": "insights"},  # 자리 이름은 insight다
        {"flow": "loop"},
        {"status": "running"},  # 그런 상태는 없다
        {"status": "aborted"},  # 대기인 제안을 닫을 때만 생긴다(/close)
        {"stop_reason": ""},
        {"steps": -1},
    ],
)
def test_refuses_values_outside_the_lists(overrides):
    with pytest.raises(ValidationError):
        RunWrite.model_validate(run_body(**overrides))


def test_call_ids_are_unique_in_a_run():
    twice = [{"call_id": "c1", "tool": "t", "args": {}}] * 2
    with pytest.raises(ValidationError, match="call_id"):
        RunWrite.model_validate(run_body(tool_calls=twice))
