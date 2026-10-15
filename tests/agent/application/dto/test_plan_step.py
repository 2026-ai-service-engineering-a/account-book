from __future__ import annotations

from agent.application.dto import PlanStep


def test_arguments_that_were_not_json_are_none():
    assert PlanStep("detect_outliers", None, "큰 건").arguments is None
