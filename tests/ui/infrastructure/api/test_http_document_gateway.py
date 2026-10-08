from __future__ import annotations

import asyncio
from datetime import date

import pytest

from tests.ui.infrastructure.api.conftest import client, recorder
from ui.application.dto import ChunkStrategy, SearchMode
from ui.application.errors import LedgerUnavailable
from ui.infrastructure.api import HttpDocumentGateway

HIT = {
    "id": "paragraph:조세특례제한법 시행령/제121조의2/16",
    "document_id": "조세특례제한법 시행령",
    "title": "조세특례제한법 시행령",
    "effective_date": "2026-09-18",
    "strategy": "paragraph",
    "heading": "제121조의2(신용카드등 사용금액에 대한 소득공제) <16>",
    "body": "<16> 법 제126조의2제2항제3호다목 … 수영장 및 체력단련장을 말한다.",
    "score": 0.62,
}


def test_asks_by_strategy_and_reads_the_hits():
    handler, seen = recorder(body=[HIT])
    gateway = HttpDocumentGateway(client(handler))
    found = asyncio.run(gateway.search("체력단련장", ChunkStrategy.PARAGRAPH, 3))
    (hit,) = found.hits
    assert found.mode is SearchMode.KEYWORD and not found.fell_back
    assert dict(seen[0].url.params) == {"q": "체력단련장", "k": "3", "strategy": "paragraph"}
    assert seen[0].url.path == "/v1/documents/search"
    assert (hit.title, hit.effective_date, hit.score) == (
        "조세특례제한법 시행령",
        date(2026, 9, 18),
        0.62,
    )


def test_strange_body_is_unavailable():
    handler, _ = recorder(body={"not": "a list"})
    with pytest.raises(LedgerUnavailable):
        asyncio.run(HttpDocumentGateway(client(handler)).search("x", ChunkStrategy.PARAGRAPH))


def test_asking_for_meaning_without_an_agent_says_it_fell_back():
    handler, _ = recorder(body=[HIT])
    gateway = HttpDocumentGateway(client(handler))
    found = asyncio.run(gateway.search("x", ChunkStrategy.PARAGRAPH, 3, SearchMode.HYBRID))
    assert found.mode is SearchMode.KEYWORD and found.fell_back
