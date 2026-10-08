from __future__ import annotations

from agent.application.dto import ToolCall, ToolError, ToolMeta, ToolResult, ToolStep
from agent.application.use_cases import document_sources as docs

WITHDRAW = {
    "ref": "d1a2b3c",
    "title": "할부거래에 관한 법률",
    "heading": "제8조 ① 1.",
    "effective_date": "2025-01-01",
    "body": "계약서를 받은 날부터 7일",
}
TRANSIT = WITHDRAW | {"ref": "d4e5f60", "title": "조세특례제한법", "heading": "제126조의2 ② 2."}


def found(*chunks: dict[str, str], name: str = "search_documents") -> ToolStep:
    meta = ToolMeta(len(chunks), False, 3, {})
    return ToolStep(
        ToolCall("c1", name, {"query": "q"}), ToolResult("c1", {"chunks": list(chunks)}, meta)
    )


def test_chunks_from_every_search_once_each():
    failed = ToolStep(
        ToolCall("c3", "search_documents", {"query": "q"}),
        ToolResult("c3", error=ToolError("internal_error", True, "다시")),
    )
    steps = [found(WITHDRAW), found(WITHDRAW, TRANSIT), failed, found(TRANSIT, name="x")]
    assert list(docs.documents_in(steps)) == ["d1a2b3c", "d4e5f60"]


def test_refs_in_order_brackets_or_bare():
    text = "7일이에요 [d4e5f60, d1a2b3c]. 다시 d4e5f60 참고. adeadbeef는 아니다"
    assert docs.refs_in(text) == ["d4e5f60", "d1a2b3c"]
    assert docs.without_refs("7일 [d1a2b3c]") == "7일 []"


def test_refs_become_numbers_and_sources_are_written_by_code():
    refs = ["d4e5f60", "d1a2b3c"]
    assert docs.numbered("둘 다 돼요 [d4e5f60, d1a2b3c]. 또 d1a2b3c.", refs) == (
        "둘 다 돼요 [1, 2]. 또 [2]."
    )
    documents = docs.documents_in([found(WITHDRAW, TRANSIT)])
    assert docs.source_lines(refs, documents) == (
        "출처\n"
        "[1] 조세특례제한법 제126조의2 ② 2. · 시행 2025-01-01\n"
        "[2] 할부거래에 관한 법률 제8조 ① 1. · 시행 2025-01-01"
    )
    assert docs.source_lines([], documents) == ""


def test_uncited_searches_show_where_they_looked():
    documents = docs.documents_in([found(WITHDRAW)])
    assert docs.found_lines(documents) == (
        "찾은 조문\n- 할부거래에 관한 법률 제8조 ① 1. · 시행 2025-01-01"
    )
    assert docs.found_lines({}) == ""


def test_sources_hold_the_place_and_the_body():
    assert docs.sources({"d1a2b3c": WITHDRAW}) == {
        "d1a2b3c": "할부거래에 관한 법률 제8조 ① 1.\n계약서를 받은 날부터 7일"
    }
