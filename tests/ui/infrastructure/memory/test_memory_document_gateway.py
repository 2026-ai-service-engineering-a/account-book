from __future__ import annotations

import asyncio

from ui.application.dto import ChunkStrategy, DocumentHit
from ui.infrastructure.memory import MemoryDocumentGateway


def search(query: str, k: int = 5) -> tuple[DocumentHit, ...]:
    return asyncio.run(MemoryDocumentGateway().search(query, ChunkStrategy.PARAGRAPH_ITEM, k)).hits


def test_ranks_by_shared_trigrams():
    hits = search("수영장 및 체력단련장", k=2)
    assert len(hits) == 2 and hits[0].title == "조세특례제한법 시행령"
    assert hits[0].id.startswith("paragraph_item:") and hits[0].score > hits[1].score


def test_blank_finds_nothing():
    assert search("   ") == ()
