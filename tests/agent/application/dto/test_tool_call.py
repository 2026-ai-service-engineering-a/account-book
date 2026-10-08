from __future__ import annotations

from agent.application.dto import ToolCall


def test_holds_what_the_model_said_unchecked():
    call = ToolCall("call_1", "count_frequency", {"period": "last_week"})
    assert call.arguments["period"] == "last_week"
