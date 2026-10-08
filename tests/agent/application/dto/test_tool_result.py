from __future__ import annotations

from datetime import datetime

import pytest

from agent.application.dto import ToolError, ToolMeta, ToolResult
from agent.domain.values import TimeRange
from tests.agent.conftest import SEOUL

WEEK = TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL))


def test_success_envelope_matches_tools_md():
    meta = ToolMeta(7, False, 38, {"period": WEEK})
    result = ToolResult("call_3", {"count": 7}, meta)
    assert result.ok
    assert result.envelope() == {
        "call_id": "call_3",
        "ok": True,
        "data": {"count": 7},
        "meta": {
            "row_count": 7,
            "truncated": False,
            "elapsed_ms": 38,
            "periods": {
                "period": {"from": "2026-09-28T00:00:00+09:00", "to": "2026-10-05T00:00:00+09:00"}
            },
        },
    }


def test_failure_is_an_envelope_too():
    result = ToolResult("call_2", error=ToolError("validation_error", True, "period를 고쳐라"))
    assert not result.ok
    assert result.envelope() == {
        "call_id": "call_2",
        "ok": False,
        "error": {"code": "validation_error", "retryable": True, "hint": "period를 고쳐라"},
    }


def test_note_shows_only_when_there_is_one():
    meta = ToolMeta(20, True, 1, note="더 있다")
    assert ToolResult("c", {"x": 1}, meta).envelope()["meta"]["note"] == "더 있다"  # type: ignore[index]


@pytest.mark.parametrize(
    "build",
    [lambda: ToolResult("c"), lambda: ToolResult("c", {}, error=ToolError("x", False, "y"))],
)
def test_exactly_one_of_data_or_error(build):
    with pytest.raises(ValueError):
        build()
