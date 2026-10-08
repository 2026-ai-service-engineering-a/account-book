from __future__ import annotations


def test_empty_page_suggests_words_from_the_law(client):
    page = client.get("/documents")
    assert page.status_code == 200 and "조문에 나오는 낱말로 찾아보세요." in page.text
    assert 'aria-current="page"' in page.text and 'href="/documents"' in page.text


def test_results_quote_the_text_with_the_effective_date(client):
    page = client.get("/documents", params={"q": "체력단련장", "strategy": "paragraph_item"})
    assert "조세특례제한법 시행령 제121조의2" in page.text
    assert "시행 2026-09-18" in page.text and "법률 자문이 아닙니다" in page.text
    assert '<option value="paragraph_item" selected>' in page.text


def test_unknown_strategy_falls_back_to_the_measured_default(client):
    page = client.get("/documents", params={"q": "체력단련장", "strategy": "whole"})
    assert '<option value="paragraph_item" selected>' in page.text


def test_without_an_agent_there_is_no_mode_to_choose(client):
    page = client.get("/documents", params={"q": "체력단련장", "mode": "vector"})
    assert 'name="mode"' not in page.text and "AI 검색" not in page.text
    assert "낱말로 찾았어요" not in page.text  # 고를 수 없었으니 물러선 것도 아니다


def test_with_an_agent_the_page_says_ai_and_offers_modes():
    from fastapi.testclient import TestClient

    from tests.ui.conftest import FixedClock
    from ui.infrastructure.settings import Settings
    from ui.main import create_app

    # agent 주소만 있고 떠 있지는 않다 — 물러서서 대역의 낱말 검색으로 찾는다
    settings = Settings(
        _env_file=None, agent_base_url="http://127.0.0.1:9", agent_timeout_seconds=0.1
    )
    client = TestClient(create_app(settings, clock=FixedClock(), seeded=False))
    page = client.get("/documents", params={"q": "체력단련장"})  # 방법을 고르지 않으면 하이브리드
    assert "AI 검색" in page.text and '<option value="hybrid" selected>' in page.text
    assert "낱말로 찾았어요" in page.text and "제121조의2" in page.text


def test_asking_without_an_agent_shows_the_found_clauses_folded(client):
    page = client.get("/documents", params={"q": "체력단련장", "action": "ask"})
    assert "답 대신 찾은 조문을 보여 드려요." in page.text and "각본 대역" in page.text
    assert "<details" in page.text and "법률 자문이 아닙니다" in page.text


def test_a_cited_answer_shows_its_sources_to_unfold(client):
    import dataclasses
    from datetime import date

    from ui.application.dto import AnswerStatus, ChunkStrategy, DocumentAnswer, DocumentHit

    hit = DocumentHit(
        "paragraph_item:할부거래에 관한 법률/제8조/1/1",
        "할부거래에 관한 법률",
        date(2026, 9, 8),
        ChunkStrategy.PARAGRAPH_ITEM,
        "제8조(청약의 철회) ① 1.",
        "- 1. 계약서를 받은 날부터 7일",
        0.03,
    )

    class Answered:
        async def ask(self, question: str) -> DocumentAnswer:
            return DocumentAnswer(
                AnswerStatus.ANSWERED, "7일 안에 철회할 수 있어요.", (hit,), (hit,)
            )

    app = client.app
    app.state.services = dataclasses.replace(app.state.services, answerer=Answered())
    page = client.get("/documents", params={"q": "노트북 취소", "action": "ask"})
    assert "AI 답" in page.text and "7일 안에 철회할 수 있어요." in page.text
    assert "할부거래에 관한 법률 제8조(청약의 철회) ① 1. · 시행 2026-09-08" in page.text
