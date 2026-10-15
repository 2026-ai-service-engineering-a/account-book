from __future__ import annotations

from mcp_server.domain.tools import ToolContract, ToolName


def test_holds_a_line_of_the_contract():
    line = ToolContract(ToolName.SUMMARIZE_SPENDING, "합을 낸다", {"type": "object"})
    assert line.name.value == "summarize_spending" and line.input_schema["type"] == "object"
