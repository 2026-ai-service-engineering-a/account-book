from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from tests.ui.conftest import SEOUL
from ui.application.dto import RunLine
from ui.application.values import RunId


def line(run_id: str = "r1", **overrides: object) -> RunLine:
    values: dict[str, object] = {
        "id": RunId(run_id),
        "seat": "insight",
        "flow": "plan_execute",
        "utterance": "2026-09",
        "model": "gemini/gemini-flash-lite-latest",
        "steps": 2,
        "tokens": 1240,
        "cost_usd": Decimal("0.000210"),
        "status": "done",
        "stop_reason": "assembled",
        "client": None,
        "created_at": datetime(2026, 10, 15, 13, 57, tzinfo=SEOUL),
        "tool_count": 2,
    }
    return RunLine(**(values | overrides))  # type: ignore[arg-type]


def test_holds_the_audit_columns_as_the_api_gave_them():
    found = line()
    assert (found.seat, found.status, found.tool_count) == ("insight", "done", 2)
