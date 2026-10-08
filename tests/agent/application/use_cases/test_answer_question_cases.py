"""평가 세트(questions.json)의 모양 — 모델 없이 CI에서 돈다. 세트가 문서와 어긋나지 않게."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from agent.application.dto import (
    LoopOutcome,
    ModelUsage,
    StopReason,
    ToolCall,
    ToolMeta,
    ToolResult,
    ToolStep,
)
from agent.domain.tools import Mode
from agent.domain.values import PeriodName, TimeRange
from tests.agent.application.use_cases.test_answer_question_eval import cited, has_product
from tests.agent.conftest import SEOUL

FIXTURE = Path(__file__).parents[3] / "fixtures" / "ai" / "questions.json"
CATEGORIES = {"food", "cafe", "transport", "living", "housing", "etc", "salary", "other_income"}


def cases() -> list[dict[str, object]]:
    found = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    assert isinstance(found, list)
    return found


LAWS = {
    path.read_text(encoding="utf-8").split("\n", 1)[0].removeprefix("# ")
    for path in (FIXTURE.parent / "documents" / "laws").glob("*.md")
}


def test_thirty_eight_questions_in_the_groups_of_chapter_nine_and_the_document_tool():
    assert Counter(c["group"] for c in cases()) == {
        "single": 15,
        "period": 8,
        "pair": 4,
        "refuse": 3,
        "document": 5,  # document-rag.md 5.5
        "combo": 3,
    }
    assert len({c["question"] for c in cases()}) == 38


def test_document_questions_name_a_law_we_have():
    for case in cases():
        if case["group"] in ("document", "combo"):
            assert case["law"] in LAWS, case["question"]
        if case["group"] == "combo":
            named = set(case["tools"])  # type: ignore[call-overload]
            assert "search_documents" in named and len(named) == 2, case["question"]


def test_labels_use_only_query_tools_period_names_and_known_categories():
    tools = {t.value for t in Mode.QUERY.tools}
    for case in cases():
        named = [case["tool"]] if "tool" in case else list(case.get("tools", []))  # type: ignore[call-overload]
        assert set(named) <= tools, case["question"]
        for key in ("period", "a", "b"):
            if key in case:
                PeriodName(case[key]["name"])  # type: ignore[index]
        if "category_id" in case:
            assert case["category_id"] in CATEGORIES, case["question"]


def test_grading_sees_a_product_only_when_it_reaches_the_screen():
    """채점 함수의 손 점검 — 실제 모델 없이(test_answer_question_eval.py의 has_product·cited)."""
    today = date(2026, 10, 8)
    month = TimeRange(datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 11, 1, tzinfo=SEOUL))
    chunk = {"ref": "d4e5f60", "title": "조세특례제한법", "heading": "제126조의2 ② 2.",
             "effective_date": "2025-01-01", "body": "대중교통이용분의 100분의 40"}  # fmt: skip

    def spent(*amounts: int) -> ToolStep:
        data = {"expense": [{"amount": a, "currency": "KRW"} for a in amounts]}
        meta = ToolMeta(1, False, 3, {"period": month})
        return ToolStep(ToolCall("c1", "x", {}), ToolResult("c1", data, meta))

    laws = ToolStep(
        ToolCall("c2", "search_documents", {"query": "q"}),
        ToolResult("c2", {"chunks": [chunk]}, ToolMeta(1, False, 3, {})),
    )

    def outcome(text: str, *amounts: int) -> LoopOutcome:
        steps = (spent(*amounts), laws)
        return LoopOutcome(StopReason.ANSWERED, text, steps, ModelUsage(), 2)

    dropped = outcome("52,000원의 40%인 20,800원이에요 [d4e5f60].", 52_000)
    assert not has_product(dropped, today)  # answer_text가 문장을 버렸다
    assert not cited(dropped, "조세특례제한법", today)
    leaked = outcome("20,800원이고 40%예요 [d4e5f60].", 52_000, 20_800)  # 우연히 도구에 있는 수
    assert has_product(leaked, today)
    assert cited(outcome("40%를 공제해요 [d4e5f60].", 52_000), "조세특례제한법", today)
