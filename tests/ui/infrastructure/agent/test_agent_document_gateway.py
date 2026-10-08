from __future__ import annotations

import asyncio
import json

import httpx

from ui.application.dto import ChunkStrategy, SearchMode
from ui.infrastructure.agent import AgentDocumentGateway
from ui.infrastructure.memory import MemoryDocumentGateway

CHUNK = {
    "id": "hybrid:할부거래에 관한 법률/제8조/1",
    "title": "할부거래에 관한 법률",
    "effective_date": "2026-09-08",
    "strategy": "paragraph",
    "heading": "제8조(청약의 철회) ①",
    "body": "① 소비자는 … 철회할 수 있다.",
    "score": 0.031,
}


def gateway(handler) -> AgentDocumentGateway:
    transport = httpx.MockTransport(handler)
    return AgentDocumentGateway("http://agent", 1, MemoryDocumentGateway(), transport=transport)


def test_asks_the_agent_and_keeps_the_mode_it_used():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"mode": "hybrid", "fell_back": False, "chunks": [CHUNK]})

    found = asyncio.run(
        gateway(handler).search("노트북 취소", ChunkStrategy.PARAGRAPH, 3, SearchMode.HYBRID)
    )
    assert json.loads(seen[0].content) == {
        "q": "노트북 취소",
        "k": 3,
        "strategy": "paragraph",
        "mode": "hybrid",
    }
    assert found.mode is SearchMode.HYBRID and not found.fell_back
    assert found.hits[0].title == "할부거래에 관한 법률"


def test_an_agent_that_fell_back_is_believed():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"mode": "keyword", "fell_back": True, "chunks": []})

    found = asyncio.run(gateway(handler).search("x", ChunkStrategy.PARAGRAPH, 3, SearchMode.VECTOR))
    assert (found.mode, found.fell_back) == (SearchMode.KEYWORD, True)


def test_a_dead_agent_falls_back_to_keyword_search():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    found = asyncio.run(
        gateway(handler).search("체력단련장", ChunkStrategy.PARAGRAPH, 2, SearchMode.VECTOR)
    )
    assert found.fell_back and found.mode is SearchMode.KEYWORD and len(found.hits) == 2
