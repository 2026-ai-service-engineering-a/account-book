from __future__ import annotations

from agent.application.dto import ToolCallRecord


def test_keeps_the_arguments_as_they_were():
    call = ToolCallRecord("c1", "suggest_category", {"merchant": "블루보틀"}, None)
    assert call.args == {"merchant": "블루보틀"} and call.result is None
