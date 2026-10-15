from __future__ import annotations

from decimal import Decimal

from api.application.dto import RunRecord
from api.domain.values import RunFlow, RunSeat, RunStatus


def run_record(run_id: str = "r1", **overrides: object) -> RunRecord:
    values: dict[str, object] = {
        "id": run_id,
        "seat": RunSeat.CHAT,
        "flow": RunFlow.REACT,
        "utterance": "이번 달 카페에 얼마 썼어?",
        "model": "gemini/flash",
        "steps": 2,
        "tokens": 120,
        "cost_usd": Decimal("0.000150"),
        "status": RunStatus.DONE,
        "stop_reason": "answered",
    }
    return RunRecord(**(values | overrides))  # type: ignore[arg-type]


def test_no_tool_calls_by_default():
    assert run_record().tool_calls == ()
