from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent.domain.tools import Mode, Permission, ToolName

SNAPSHOTS = Path(__file__).parents[3] / "fixtures" / "ai" / "tool_schemas"
WRITES = {
    ToolName.CREATE_TRANSACTION,
    ToolName.UPDATE_TRANSACTION,
    ToolName.DELETE_TRANSACTION,
    ToolName.SET_BUDGET,
}


def test_query_mode_has_no_write_tool():
    # 조회를 물었는데 거래가 지워질 길이 구조적으로 없어야 한다(chat-analytics 2장)
    assert not WRITES & set(Mode.QUERY.tools)
    assert all(t.permission is Permission.READ for t in Mode.QUERY.tools)


def test_query_mode_is_the_five_from_chat_analytics_and_document_search():
    assert {t.value for t in Mode.QUERY.tools} == {
        "summarize_spending",
        "count_frequency",
        "compare_periods",
        "get_budget_status",
        "search_transactions",
        "search_documents",
    }


def test_only_the_query_mode_searches_documents():
    assert [m for m in Mode if ToolName.SEARCH_DOCUMENTS in m.tools] == [Mode.QUERY]


def test_classify_mode_only_suggests():
    assert Mode.CLASSIFY.tools == (ToolName.SUGGEST_CATEGORY,)


def test_no_mode_lists_a_tool_twice():
    for mode in Mode:
        assert len(set(mode.tools)) == len(mode.tools), mode


def schema_of(mode: Mode) -> list[dict[str, object]]:
    return [
        {"name": s.name.value, "description": s.description, "input_schema": s.input_schema}
        for s in mode.specs()
    ]


@pytest.mark.parametrize("mode", list(Mode))
def test_what_the_model_sees_is_pinned(mode):
    """이 파일이 바뀌면 모델에게 주는 프롬프트가 바뀐 것이다 — 리뷰에서 보여야 한다(tools.md 8장).

    의도한 변경이면 UPDATE_SNAPSHOTS=1로 한 번 돌려 파일을 다시 쓰고 같이 커밋한다.
    """
    path = SNAPSHOTS / f"{mode.value}.json"
    current = json.dumps(schema_of(mode), ensure_ascii=False, indent=2) + "\n"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        path.write_text(current, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == current, f"{path.name}가 바뀌었다"
