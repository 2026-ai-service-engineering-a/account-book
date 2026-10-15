from __future__ import annotations

from mcp_server.domain.tools import ToolName


def test_the_four_aggregates_and_nothing_that_writes_or_lists():
    assert {t.value for t in ToolName} == {
        "summarize_spending",
        "compare_periods",
        "count_frequency",
        "get_budget_status",
    }
