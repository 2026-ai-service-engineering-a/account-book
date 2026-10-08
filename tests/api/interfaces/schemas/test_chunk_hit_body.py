from __future__ import annotations

from datetime import date

from api.application.dto import ChunkHit
from api.domain.entities import DocumentChunk
from api.domain.values import ChunkId, ChunkStrategy, DocumentId
from api.interfaces.schemas import ChunkHitBody


def test_carries_the_source_and_a_rounded_score():
    chunk = DocumentChunk(
        ChunkId("paragraph:법/제1조/1"), DocumentId("법"), ChunkStrategy.PARAGRAPH,
        "제1조(목적) ①", "① 목적이다. <개정 2020.1.1>", "① 목적이다.", "h", 1,
    )  # fmt: skip
    body = ChunkHitBody.of(ChunkHit(chunk, 0.123456, "법", date(2026, 10, 1))).model_dump()
    assert body["score"] == 0.1235 and body["effective_date"] == date(2026, 10, 1)
    assert body["body"].endswith("<개정 2020.1.1>")  # 화면의 인용은 원문이다
    assert "search_text" not in body
