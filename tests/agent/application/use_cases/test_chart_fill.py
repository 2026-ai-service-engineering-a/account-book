from __future__ import annotations

from agent.application.dto import ChartSpec, ToolCall, ToolResult, ToolStep
from agent.application.use_cases.chart_fill import fill_chart

ROWS = {
    "changes": [
        {"name": "생활", "delta": {"amount": 890000, "currency": "KRW"}},
        {"name": "식비", "delta": {"amount": -12000, "currency": "KRW"}},
    ]
}
STEP = ToolStep(ToolCall("call_3", "compare_periods", {}), ToolResult("call_3", data=ROWS))


def spec(**overrides: object) -> ChartSpec:
    values: dict[str, object] = {
        "kind": "bar",
        "title": "달라진 것",
        "source": "call_3",
        "x_field": "name",
        "y_field": "delta",
        "unit": "KRW",
        "annotate": ("생활", "식비", "교통"),
    }
    return ChartSpec(**(values | overrides))  # type: ignore[arg-type]


def test_values_come_from_the_result_not_the_model():
    drawn = fill_chart(spec(), [STEP])
    assert drawn is not None
    assert [(p.label, p.value, p.annotated) for p in drawn.points] == [
        ("생활", 890000, True),
        ("식비", -12000, True),
    ]


def test_a_row_without_the_field_drops_the_chart_rather_than_drawing_zero():
    rows = {"changes": [*ROWS["changes"], {"name": "교통"}]}
    step = ToolStep(STEP.call, ToolResult("call_3", data=rows))
    assert fill_chart(spec(), [step]) is None


def test_a_result_without_rows_has_nothing_to_draw():
    empty = ToolStep(STEP.call, ToolResult("call_3", data={"changes": []}))
    assert fill_chart(spec(), [empty]) is None
