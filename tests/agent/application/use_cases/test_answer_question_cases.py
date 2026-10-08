"""평가 세트(questions.json)의 모양 — 모델 없이 CI에서 돈다. 세트가 문서와 어긋나지 않게."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from agent.domain.tools import Mode
from agent.domain.values import PeriodName

FIXTURE = Path(__file__).parents[3] / "fixtures" / "ai" / "questions.json"
CATEGORIES = {"food", "cafe", "transport", "living", "housing", "etc", "salary", "other_income"}


def cases() -> list[dict[str, object]]:
    found = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    assert isinstance(found, list)
    return found


def test_thirty_questions_in_the_groups_of_chapter_nine():
    assert Counter(c["group"] for c in cases()) == {
        "single": 15,
        "period": 8,
        "pair": 4,
        "refuse": 3,
    }
    assert len({c["question"] for c in cases()}) == 30


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
