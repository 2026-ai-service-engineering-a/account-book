from __future__ import annotations

from mcp_server.domain.tools import ToolName, ToolRequest
from mcp_server.domain.values import PeriodName, PeriodSpec


def test_narrows_nothing_by_default():
    request = ToolRequest(ToolName.SUMMARIZE_SPENDING, {"period": PeriodSpec(PeriodName.TODAY)})
    assert (request.category_id, request.merchant, request.direction) == ("", "", None)
