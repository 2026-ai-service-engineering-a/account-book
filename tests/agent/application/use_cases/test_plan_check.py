from __future__ import annotations

from agent.application.dto import PlanStep, ToolCall
from agent.application.use_cases.plan_check import checked_plan
from agent.domain.tools import Mode

FIXED = [ToolCall("call_1", "summarize_spending", {"period": "this_month"})]


def step(tool: str, **args: object) -> PlanStep:
    return PlanStep(tool, args, "")


def test_keeps_in_order_numbers_after_the_called_and_stops_at_the_limit():
    steps = [step("detect_outliers", period="this_month"), step("count_frequency", period="x")]
    steps += [step("compare_periods", a="last_month", b="this_month")] * 2
    steps += [step("get_budget_status", period="last_month")]
    kept = checked_plan(steps, Mode.INSIGHT.tools, FIXED, 2, 2)
    assert [(c.call_id, c.name) for c, _ in kept] == [
        ("call_2", "detect_outliers"),
        ("call_3", "compare_periods"),
    ]


def test_drops_what_was_already_called_and_tools_outside_the_mode():
    steps = [step("summarize_spending", period="this_month"), step("search_documents", query="q")]
    assert checked_plan(steps, Mode.INSIGHT.tools, FIXED, 4, 2) == ()
    assert checked_plan([PlanStep("detect_outliers", None, "")], Mode.INSIGHT.tools, [], 4, 1) == ()
