from __future__ import annotations

from agent.application.dto import ToolCall, ToolResult, ToolStep


def test_call_and_its_envelope():
    step = ToolStep(ToolCall("c1", "count_frequency", {}), ToolResult("c1", {"count": 0}))
    assert step.result.ok
