"""리포트 흐름의 테이프 — 정해진 LLM 응답과 정해진 도구 응답으로 같은 길을 밟는지 본다
(ai/agent-loop.md 10장). 모델은 부르지 않는다(development-rules 4.3)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime

import pytest

from agent.application.dto import Insight, InsightStop
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.use_cases import BuildInsights, Retrieve
from agent.domain.tools import (
    BudgetLine,
    CategoryShift,
    Frequency,
    OutlierLine,
    OutlierReport,
    SpendingTotals,
)
from agent.domain.values import Amount, CategoryId, TimeRange
from tests.agent.conftest import SEOUL, FakeEmbedder, FakeLedger, FakeModel

SEPTEMBER = date(2026, 9, 1)
TODAY = date(2026, 10, 15)


def _line(category: str, name: str, spent: int) -> BudgetLine:
    return BudgetLine(CategoryId(category), name, Amount(spent), None, None, None, None, None)


BUDGETS = (_line("food", "식비", 412_000), _line("living", "생활", 1_050_000))
BIG = OutlierLine(
    "t1",
    datetime(2026, 9, 14, 15, tzinfo=SEOUL),
    CategoryId("living"),
    "전자랜드",
    Amount(890_000),
    Amount(52_000),
    Amount(89_000),
)
BASELINE = TimeRange(datetime(2026, 3, 1, tzinfo=SEOUL), datetime(2026, 9, 1, tzinfo=SEOUL))
SHIFT = CategoryShift(
    CategoryId("living"), "생활", Amount(160_000), Amount(1_050_000), Amount(890_000), 556
)


def ledger(**overrides: object) -> FakeLedger:
    replies: dict[str, object] = {
        "summary": SpendingTotals(Amount(1_462_000), Amount(3_200_000)),
        "budget_status": BUDGETS,
        "outliers": OutlierReport(BASELINE, (BIG,), False, ()),
        "compare": (SHIFT,),
        "frequency": Frequency(21, 18, 1.4, Amount(19_600)),
    }
    return FakeLedger(replies=replies | overrides)


def plan(*steps: tuple[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        "steps": [
            {"tool": tool, "args": json.dumps(args), "why": f"{tool}를 보려고"}
            for tool, args in steps
        ]
    }


def chart(source: str = "call_2", **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "kind": "hbar",
        "title": "9월에 어디에 썼나",
        "source": source,
        "x_field": "name",
        "y_field": "spent",
        "unit": "KRW",
        "annotate": ["생활"],
        "note": "",
    }
    return base | overrides


def assembled(charts: Sequence[object], *texts: str) -> dict[str, object]:
    return {"charts": list(charts), "highlights": [{"text": t, "source": "call_3"} for t in texts]}


OUTLIERS = ("detect_outliers", {"period": "this_month"})
COMPARE = ("compare_periods", {"a": "last_month", "b": "this_month"})
SAID = "생활에 전자랜드 890,000원 한 건이 있었어요."


def build(
    model: FakeModel, found: FakeLedger | None = None, month: date = SEPTEMBER
) -> tuple[Insight, FakeLedger]:
    found = found or ledger()
    flow = BuildInsights(model, found, Retrieve(found, FakeEmbedder(), None), 6, lambda: 0.0)
    return asyncio.run(flow(month, TODAY, SEOUL)), found


def test_scan_then_plan_then_run_together_then_assemble():
    model = FakeModel(plan(OUTLIERS, COMPARE), assembled([chart()], SAID))
    insight, found = build(model)
    # 고정 둘이 먼저, 계획한 둘이 그 뒤 — 9월 리포트는 9월을 본다
    assert [m for m, _ in found.calls] == ["summary", "budget_status", "outliers", "compare"]
    assert found.calls[1][1][0] == SEPTEMBER
    assert insight.stop is InsightStop.ASSEMBLED and insight.model_calls == 2
    (drawn,) = insight.charts
    assert [(p.label, p.value, p.annotated) for p in drawn.points] == [
        ("식비", 412_000, False),
        ("생활", 1_050_000, True),
    ]
    assert insight.highlights == (SAID,)
    assert insight.whys == {
        "call_3": "detect_outliers를 보려고",
        "call_4": "compare_periods를 보려고",
    }


def test_last_month_is_the_month_before_the_report_not_before_today():
    model = FakeModel(plan(COMPARE), assembled([chart()]))
    _, found = build(model)
    a, b, _ = next(args for m, args in found.calls if m == "compare")
    assert a == TimeRange(datetime(2026, 8, 1, tzinfo=SEOUL), datetime(2026, 9, 1, tzinfo=SEOUL))
    assert isinstance(b, TimeRange) and b.start == datetime(2026, 9, 1, tzinfo=SEOUL)


def test_the_plan_table():
    steps = plan(
        ("search_transactions", {"period": "this_month"}),  # 이 모드의 도구가 아니다
        ("detect_outliers", {"threshold": 2}),  # 인자가 스키마 밖이다
        ("summarize_spending", {"period": "this_month"}),  # 고정 호출과 같다
        OUTLIERS,
        OUTLIERS,  # 계획 안에서 겹친다
        COMPARE,
        ("count_frequency", {"period": "this_month"}),
        ("count_frequency", {"period": "last_month"}),
        ("summarize_spending", {"period": "last_month"}),  # 상한(6 - 고정 2 = 4)을 넘는다
    )
    steps["steps"][1]["args"] = "{not json"  # type: ignore[index]  # 인자가 JSON이 아니다
    insight, _ = build(FakeModel(steps, assembled([])))
    assert [s.call.name for s in insight.steps[2:]] == [
        "detect_outliers",
        "compare_periods",
        "count_frequency",
        "count_frequency",
    ]
    assert [s.call.call_id for s in insight.steps] == [f"call_{n}" for n in range(1, 7)]


def test_nothing_more_to_see_is_assembled_from_the_two_fixed_calls():
    # 빈 계획은 "더 볼 것이 없다"다 — 고정 호출에 이미 있는 것으로 말한다
    model = FakeModel(plan(), assembled([chart()], "식비는 412,000원이었어요."))
    insight, found = build(model)
    assert insight.stop is InsightStop.ASSEMBLED and insight.model_calls == 2
    assert insight.highlights == ("식비는 412,000원이었어요.",)
    assert len(found.calls) == 2  # 추가 호출은 없다


def test_replans_once_when_everything_came_back_empty():
    empty = ledger(outliers=OutlierReport(BASELINE, (), False, ()), compare=())
    model = FakeModel(
        plan(OUTLIERS),
        plan(COMPARE),  # 다시 세운 계획도 비었다 — 세 번째는 없다
        assembled([chart()]),
    )
    insight, _ = build(model, empty)
    assert insight.replanned and insight.model_calls == 3
    assert "전부 비었다" in model.prompts[1].user and "detect_outliers" in model.prompts[1].user
    assert insight.stop is InsightStop.ASSEMBLED


def test_a_plan_with_something_found_is_not_replanned():
    model = FakeModel(plan(OUTLIERS), assembled([], SAID))
    insight, _ = build(model)
    assert not insight.replanned and insight.model_calls == 2


def test_the_chart_table_drops_one_chart_at_a_time():
    charts = [
        chart(kind="pie"),  # 목록 밖의 모양
        chart(source="call_9"),  # 부르지 않은 호출
        chart(y_field="budget"),  # 결과에 없는 필드
        chart() | {"data": [412_000, 1_050_000]},  # 값 배열이 실려 왔다
        chart(source="call_1", x_field="expense", y_field="income"),  # 합계에는 행이 없다
        chart(unit="won"),  # 단위 밖
        chart(title="남는 첫째", note="생활이 1,050,000원으로 가장 크다"),
        chart(source="call_3", x_field="merchant", y_field="amount", title="남는 둘째"),
        chart(title="셋째는 넘친다"),
    ]
    insight, _ = build(FakeModel(plan(OUTLIERS), assembled(charts)))
    assert [c.title for c in insight.charts] == ["남는 첫째", "남는 둘째"]
    assert insight.charts[0].note == ""  # 숫자가 든 note는 비우고 차트는 살린다
    assert insight.charts[1].points[0].value == 890_000  # 금액 봉투에서 숫자를 꺼냈다


def test_the_sentence_table_drops_one_sentence_at_a_time():
    texts = (
        "9월 지출은 모두 2,000,000원이었어요.",  # 도구 결과에 없는 숫자
        "생활비를 아껴 쓰세요.",  # 훈계
        SAID,
        "식비는 412,000원이었어요.",
        "생활이 지난달보다 890,000원 늘었어요.",
        "넷째 줄은 읽히지 않아요.",
    )
    insight, _ = build(FakeModel(plan(OUTLIERS, COMPARE), assembled([], *texts)))
    assert insight.highlights == texts[2:5]


def test_when_everything_is_dropped_the_area_is_not_drawn():
    model = FakeModel(plan(OUTLIERS), assembled([chart(kind="pie")], "과소비예요."))
    insight, _ = build(model)
    assert insight.stop is InsightStop.DISCARDED
    assert insight.charts == () and insight.highlights == ()


@pytest.mark.parametrize("seat", ["plan", "assembly"])
def test_a_malformed_answer_is_asked_once_more_then_given_up(seat):
    bad = MalformedOutput("x")
    if seat == "plan":
        once = FakeModel(bad, plan(OUTLIERS), assembled([], SAID))
        twice = FakeModel(bad, bad)
    else:
        once = FakeModel(plan(OUTLIERS), bad, assembled([], SAID))
        twice = FakeModel(plan(OUTLIERS), bad, bad)
    assert build(once)[0].stop is InsightStop.ASSEMBLED
    assert build(twice)[0].stop is InsightStop.MALFORMED


def test_no_plan_without_the_two_fixed_calls():
    model = FakeModel()
    insight, _ = build(model, ledger(budget_status=LedgerUnavailable("down")))
    assert insight.stop is InsightStop.NO_BASE and insight.model_calls == 0
    assert model.prompts == []


def test_an_unreachable_model_goes_up():
    with pytest.raises(ModelUnavailable):
        build(FakeModel(ModelUnavailable("down")))


def test_a_failed_planned_step_is_left_empty_and_the_rest_go_on():
    model = FakeModel(plan(OUTLIERS, COMPARE), assembled([chart()]))
    insight, _ = build(model, ledger(outliers=LedgerUnavailable("down")))
    assert [s.result.ok for s in insight.steps] == [True, True, False, True]
    assert insight.stop is InsightStop.ASSEMBLED and not insight.replanned


def test_the_current_month_is_read_up_to_today():
    model = FakeModel(plan(), assembled([]))
    _, found = build(model, month=date(2026, 10, 1))
    assert found.calls[1][1][0] == date(2026, 10, 1)
