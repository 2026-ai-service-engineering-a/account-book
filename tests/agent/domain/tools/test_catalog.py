from __future__ import annotations

from agent.domain.tools import READ_TOOLS, Permission, ToolName
from agent.domain.values import PeriodName

SEVEN = {
    "search_transactions",
    "summarize_spending",
    "count_frequency",
    "compare_periods",
    "get_budget_status",
    "suggest_category",
    "search_documents",
}


def test_seven_read_tools_and_nothing_that_writes():
    assert {name.value for name in READ_TOOLS} == SEVEN
    assert all(name.permission is Permission.READ for name in READ_TOOLS)
    assert all(spec.name is name for name, spec in READ_TOOLS.items())


def test_every_description_says_when_not_to_use_it():
    for spec in READ_TOOLS.values():
        lines = spec.description.split("\n")
        assert len(lines) == 2, spec.name
        assert "쓴다" in lines[1] or "쓰지 않는다" in lines[1], spec.name


def test_period_is_a_name_never_a_date_the_model_computes():
    schema = READ_TOOLS[ToolName.COUNT_FREQUENCY].input_schema
    period = schema["properties"]["period"]  # type: ignore[index]  # JSON Schema는 중첩 dict다
    assert period["properties"]["name"]["enum"] == [n.value for n in PeriodName]
    assert period["required"] == ["name"]
    assert "from" not in period["properties"]  # 경계는 코드가 푼다


def test_schemas_are_closed_objects():
    for spec in READ_TOOLS.values():
        assert spec.input_schema["type"] == "object"
        assert spec.input_schema["additionalProperties"] is False


def test_search_documents_points_back_to_the_statistics_tools():
    spec = READ_TOOLS[ToolName.SEARCH_DOCUMENTS]
    assert spec.avoid.startswith("내 지출 숫자가 필요하면 통계 도구를")
    assert spec.input_schema["required"] == ["query"]
