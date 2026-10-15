from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from mcp_server.application.errors import InvalidArguments
from mcp_server.application.parsers import parse_arguments
from mcp_server.domain.tools import ToolName
from mcp_server.domain.values import Direction, PeriodName
from tests.mcp_server.conftest import SEOUL

# agent의 테스트도 같은 표를 통과한다 — 두 서비스가 기간을 같게 푸는지 이 표가 맞춘다
PERIOD_CASES = Path(__file__).parents[3] / "fixtures" / "shared" / "period_cases.json"
_TABLE = json.loads(PERIOD_CASES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _TABLE["cases"], ids=lambda c: f"{c['today']} {c['period']}")
def test_the_shared_period_table(case):
    arguments = {"period": case["period"]}
    if case.get("rejected"):
        with pytest.raises(InvalidArguments):
            parse_arguments(ToolName.SUMMARIZE_SPENDING, arguments)
        return
    parsed = parse_arguments(ToolName.SUMMARIZE_SPENDING, arguments)
    assert _TABLE["zone"] == "Asia/Seoul"
    found = parsed.periods["period"].bounds(date.fromisoformat(case["today"]), SEOUL)
    assert (found.start.isoformat(), found.end.isoformat()) == (case["from"], case["to"])


def test_compare_takes_two_periods():
    parsed = parse_arguments(
        ToolName.COMPARE_PERIODS,
        {"a": "last_month", "b": {"name": "this_month"}, "category_id": "food"},
    )
    assert {k: v.name for k, v in parsed.periods.items()} == {
        "a": PeriodName.LAST_MONTH,
        "b": PeriodName.THIS_MONTH,
    }
    assert parsed.category_id == "food"


def test_counting_counts_spending_unless_told():
    counted = parse_arguments(ToolName.COUNT_FREQUENCY, {"period": "this_week"})
    summed = parse_arguments(ToolName.SUMMARIZE_SPENDING, {"period": "this_week"})
    assert (counted.direction, summed.direction) == (Direction.EXPENSE, None)


@pytest.mark.parametrize(
    ("name", "arguments", "field"),
    [
        (ToolName.GET_BUDGET_STATUS, {"period": "this_month", "merchant": "스타벅스"}, "merchant"),
        (ToolName.SUMMARIZE_SPENDING, {}, "period"),
        (ToolName.SUMMARIZE_SPENDING, {"period": "this_month", "direction": "out"}, "direction"),
        (ToolName.SUMMARIZE_SPENDING, {"period": "this_month", "merchant": 3}, "merchant"),
        (ToolName.COMPARE_PERIODS, {"a": "last_month"}, "b"),
    ],
)
def test_what_the_model_must_fix_names_the_field(name, arguments, field):
    with pytest.raises(InvalidArguments) as caught:
        parse_arguments(name, arguments)
    assert caught.value.field == field


def test_text_is_trimmed_and_cut_to_the_api_limit():
    parsed = parse_arguments(
        ToolName.SUMMARIZE_SPENDING, {"period": "today", "merchant": "  " + "가" * 150}
    )
    assert parsed.merchant == "가" * 100
