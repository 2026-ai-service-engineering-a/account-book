from __future__ import annotations

from datetime import date

from agent.application.dto import RetrievedChunk
from agent.domain.values import ChunkStrategy


def test_a_quote_with_its_source():
    chunk = RetrievedChunk(
        "p:법/1", "법", date(2026, 10, 1), ChunkStrategy.PARAGRAPH, "제1조 ①", "원문", 0.5
    )
    assert (chunk.title, chunk.effective_date) == ("법", date(2026, 10, 1))
