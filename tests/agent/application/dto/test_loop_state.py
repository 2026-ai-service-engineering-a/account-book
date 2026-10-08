from __future__ import annotations

from agent.application.dto import LoopState, StopReason, ToolCall, ToolError, ToolResult

CALL = ToolCall("c1", "count_frequency", {"period": "last_week", "category_id": "cafe"})
BAD = ToolResult("c1", error=ToolError("validation_error", True, "x"))


def test_same_tool_and_arguments_in_any_key_order_is_a_repeat():
    state = LoopState(0.0)
    assert state.first_time(CALL)
    swapped = ToolCall("c2", "count_frequency", {"category_id": "cafe", "period": "last_week"})
    assert not state.first_time(swapped)


def test_two_fixes_are_allowed_the_third_failure_stops():
    state = LoopState(0.0)
    assert [state.failed_too_often(CALL, BAD) for _ in range(3)] == [False, False, True]
    assert not state.failed_too_often(CALL, ToolResult("c1", {"count": 1}))


def test_end_freezes_the_steps():
    state = LoopState(0.0, calls=2)
    outcome = state.end(StopReason.ANSWERED, "끝")
    assert (outcome.model_calls, outcome.steps, outcome.text) == (2, (), "끝")
