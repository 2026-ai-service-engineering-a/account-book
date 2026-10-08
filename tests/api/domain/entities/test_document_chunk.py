from __future__ import annotations

from api.domain.entities import DocumentChunk
from api.domain.values import ChunkId, ChunkStrategy, DocumentId


def test_body_and_search_text_are_separate():
    chunk = DocumentChunk(
        ChunkId("paragraph:법/제1조/1"),
        DocumentId("법"),
        ChunkStrategy.PARAGRAPH,
        "제1조(목적) ①",
        "① 목적이다. <개정 2020.1.1>",
        "① 목적이다.",
        "abcd",
        1,
    )
    assert "<개정" in chunk.body and "<개정" not in chunk.search_text
