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


def test_unknown_strategy_falls_back_to_paragraph(client):
    page = client.get("/documents", params={"q": "체력단련장", "strategy": "whole"})
    assert '<option value="paragraph" selected>' in page.text
