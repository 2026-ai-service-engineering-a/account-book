from __future__ import annotations

import json
from datetime import date

from agent.application.dto import ToolCall, ToolError, ToolResult, ToolStep
from agent.application.prompts import INSIGHT_SCHEMA, insight_assembly_prompt


def test_only_successful_results_go_in():
    ok = ToolStep(ToolCall("call_1", "summarize_spending", {}), ToolResult("call_1", data={}))
    failed = ToolStep(
        ToolCall("call_3", "detect_outliers", {}),
        ToolResult("call_3", error=ToolError("internal_error", True, "")),
    )
    prompt = insight_assembly_prompt("2026-09", date(2026, 9, 30), [ok, failed])
    assert "call_1" in prompt.user and "call_3" not in prompt.user


def test_the_spec_has_no_pie_and_no_place_for_values():
    # 규칙을 적어 두는 것과 표현할 수 없게 만드는 것은 다르다(agentic-reports 5장)
    item = json.loads(json.dumps(INSIGHT_SCHEMA))["properties"]["charts"]["items"]
    assert "pie" not in item["properties"]["kind"]["enum"]
    assert not {"data", "values", "points"} & set(item["properties"])
    assert item["additionalProperties"] is False
