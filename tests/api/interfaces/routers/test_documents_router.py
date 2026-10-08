from __future__ import annotations

from tests.api.application.use_cases.test_search_documents import library
from tests.api.conftest import client_with


def test_keyword_search_by_strategy():
    client = client_with(library())
    params = {"q": "수영장 및 체력단련장", "k": 3, "strategy": "paragraph_item"}
    body = client.get("/v1/documents/search", params=params).json()
    assert len(body) == 3 and body[0]["strategy"] == "paragraph_item"
    assert body[0]["id"] == "paragraph_item:조세특례제한법 시행령/제121조의2/16"
    assert body[0]["title"] == "조세특례제한법 시행령" and body[0]["effective_date"] == "2026-09-18"


def test_bad_queries_are_422():
    client = client_with(library())
    assert client.get("/v1/documents/search", params={"q": ""}).status_code == 422
    assert client.get("/v1/documents/search", params={"q": "카드", "k": 21}).status_code == 422
    bad = {"q": "카드", "strategy": "whole_doc"}
    assert client.get("/v1/documents/search", params=bad).status_code == 422
