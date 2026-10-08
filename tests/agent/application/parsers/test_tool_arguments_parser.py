from __future__ import annotations

from datetime import date

import pytest

from agent.application.errors import InvalidToolArguments
from agent.application.parsers import parse_tool_arguments
from agent.domain.tools import (
    ComparePeriodsInput,
    CountFrequencyInput,
    GetBudgetStatusInput,
    SearchDocumentsInput,
    SearchTransactionsInput,
    SuggestCategoryInput,
    ToolName,
)
from agent.domain.values import CategoryId, Direction, PeriodName, PeriodSpec

LAST_WEEK = {"name": "last_week"}


def test_the_core_table_of_chat_analytics():
    found = parse_tool_arguments(
        ToolName.COUNT_FREQUENCY, {"period": LAST_WEEK, "category_id": "cafe"}
    )
    assert found == CountFrequencyInput(PeriodSpec(PeriodName.LAST_WEEK), CategoryId("cafe"))
    assert found.direction is Direction.EXPENSE


def test_a_bare_period_name_is_taken_too():
    found = parse_tool_arguments(ToolName.SUMMARIZE_SPENDING, {"period": "this_month"})
    assert found.period == PeriodSpec(PeriodName.THIS_MONTH)  # type: ignore[union-attr]


def test_period_values_by_name():
    parse = parse_tool_arguments
    recent = parse(ToolName.SUMMARIZE_SPENDING, {"period": {"name": "last_n_days", "days": 3}})
    assert recent.period == PeriodSpec(PeriodName.LAST_N_DAYS, days=3)  # type: ignore[union-attr]
    august = parse(ToolName.GET_BUDGET_STATUS, {"period": {"name": "month", "month": "2026-08"}})
    assert august == GetBudgetStatusInput(PeriodSpec(PeriodName.MONTH, start=date(2026, 8, 1)))
    span = {"name": "range", "start": "2026-09-03", "end": "2026-09-10"}
    ranged = parse(ToolName.SUMMARIZE_SPENDING, {"period": span})
    assert ranged.period.end == date(2026, 9, 10)  # type: ignore[union-attr]


def test_too_many_days_are_cut_not_refused():
    long = {"period": {"name": "last_n_days", "days": 1000}}
    assert parse_tool_arguments(ToolName.COUNT_FREQUENCY, long).period.days == 365  # type: ignore[union-attr]


def test_compare_and_search_and_suggest():
    compare = {"a": {"name": "last_month"}, "b": "this_month", "category_id": "food"}
    assert parse_tool_arguments(ToolName.COMPARE_PERIODS, compare) == ComparePeriodsInput(
        PeriodSpec(PeriodName.LAST_MONTH), PeriodSpec(PeriodName.THIS_MONTH), CategoryId("food")
    )
    search = parse_tool_arguments(
        ToolName.SEARCH_TRANSACTIONS, {"period": "this_week", "limit": 500, "merchant": " 스타 "}
    )
    assert search == SearchTransactionsInput(
        PeriodSpec(PeriodName.THIS_WEEK), merchant="스타", limit=50
    )
    suggest = parse_tool_arguments(ToolName.SUGGEST_CATEGORY, {"merchant": "블루보틀"})
    assert suggest == SuggestCategoryInput("블루보틀")


def test_a_document_query_is_one_line_cut_at_the_api_limit():
    found = parse_tool_arguments(ToolName.SEARCH_DOCUMENTS, {"query": " 할부  철회\n기간 "})
    assert found == SearchDocumentsInput("할부 철회 기간")
    long = parse_tool_arguments(ToolName.SEARCH_DOCUMENTS, {"query": "가" * 500})
    assert len(long.query) == 200  # type: ignore[union-attr]


def test_empty_category_means_no_category():
    raw = {"period": "today", "category_id": ""}
    found = parse_tool_arguments(ToolName.SUMMARIZE_SPENDING, raw)
    assert found.category_id is None  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("name", "raw", "field"),
    [
        (ToolName.COUNT_FREQUENCY, {}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "lastweek"}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "last_n_days"}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "today", "days": 3}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "month", "month": "2026-8"}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "range", "start": "9월 3일"}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": {"name": "today", "from": "x"}}, "period"),
        (ToolName.COUNT_FREQUENCY, {"period": "today", "from": "2026-09-01"}, "from"),
        (ToolName.COUNT_FREQUENCY, {"period": "today", "direction": "out"}, "direction"),
        (ToolName.COUNT_FREQUENCY, {"period": "today", "category_id": 3}, "category_id"),
        (ToolName.SEARCH_TRANSACTIONS, {"period": "today", "limit": 0}, "limit"),
        (ToolName.GET_BUDGET_STATUS, {"period": "this_week"}, "arguments"),
        (ToolName.SUGGEST_CATEGORY, {"merchant": " "}, "arguments"),
        (ToolName.SEARCH_DOCUMENTS, {"query": ""}, "arguments"),
        (ToolName.SEARCH_DOCUMENTS, {"query": "할부", "k": 3}, "k"),
        (ToolName.DELETE_TRANSACTION, {}, "name"),
    ],
)
def test_wrong_arguments_name_the_field(name, raw, field):
    with pytest.raises(InvalidToolArguments) as error:
        parse_tool_arguments(name, raw)
    assert error.value.field == field
