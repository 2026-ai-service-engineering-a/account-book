from __future__ import annotations

from pathlib import Path

import pytest

from ui.interfaces.ai_map import BY_KEY, SEATS

# docs/ai/agent-loop.md 2장의 흐름 셋. 표시에 들어가는 이름은 이 셋 중 하나다.
FLOWS = {"단발", "ReAct", "계획 실행"}
# docs/ai/tools.md 6장의 모드
MODES = {"classify", "query", "insight", "capture", "mcp"}


def test_keys_are_unique_and_indexed():
    assert len(BY_KEY) == len(SEATS)
    assert [s.key for s in SEATS] == ["capture", "classify", "query", "insight"]


@pytest.mark.parametrize("seat", SEATS, ids=lambda s: s.key)
def test_seat_speaks_the_docs_vocabulary(seat):
    assert seat.flow in FLOWS
    assert seat.mode in MODES
    assert seat.doc.startswith("docs/ai/")
    assert seat.screens and all(path.startswith("/") for _, path in seat.screens)


def test_query_mode_has_no_write_tools():
    # chat-analytics.md 2장: 질의 모드에는 읽기 도구만 준다
    writes = {"create_transaction", "update_transaction", "delete_transaction", "set_budget"}
    assert not writes & set(BY_KEY["query"].tools)
    assert not writes & set(BY_KEY["insight"].tools)


def test_only_the_query_seat_searches_documents():
    # document-rag.md 5.5: search_documents는 query 모드에만
    assert [s.key for s in SEATS if "search_documents" in s.tools] == ["query"]


@pytest.mark.parametrize(
    ("key", "path"),
    [(seat.key, path) for seat in SEATS for _, path in seat.screens],
)
def test_every_listed_screen_shows_the_badge(client, key, path):
    # 목록이 말하는 화면에 실제로 AI 표시가 있어야 한다 — 목록과 화면이 어긋나지 않게
    page = client.get(path)
    assert f'href="/wiki#{key}"' in page.text


@pytest.mark.parametrize("seat", SEATS, ids=lambda s: s.key)
def test_cited_doc_exists(seat):
    # 위키가 가리키는 정본이 옮겨지거나 지워지면 여기서 걸린다
    assert Path(seat.doc.split()[0]).is_file()


def test_capture_classify_and_query_have_a_real_agent():
    assert {s.key for s in SEATS if s.live} == {"capture", "classify", "query"}
