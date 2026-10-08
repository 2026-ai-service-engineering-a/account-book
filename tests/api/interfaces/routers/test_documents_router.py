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


def test_post_searches_by_mode_with_the_agents_vector():
    from tests.api.application.use_cases.test_search_documents_modes import (
        MODEL,
        TARGET,
        embedded,
        vector_of,
    )

    uow = embedded()
    body = {
        "q": "노트북 취소",
        "k": 2,
        "mode": "vector",
        "embedding_model": MODEL,
        "query_vector": list(vector_of(uow, TARGET)),
    }
    found = client_with(uow).post("/v1/documents/search", json=body).json()
    assert found[0]["id"] == TARGET and len(found) == 2


def test_post_vector_without_a_vector_is_422():
    response = client_with(library()).post(
        "/v1/documents/search", json={"q": "카드", "mode": "hybrid"}
    )
    assert response.status_code == 422
    assert "query_vector" in response.json()["error"]["details"]
