from __future__ import annotations

from datetime import date

from ui.application.dto import ChunkStrategy, DocumentHit


def test_a_quote_with_its_source():
    hit = DocumentHit(
        "p:법/1", "법", date(2026, 10, 1), ChunkStrategy.PARAGRAPH, "제1조 ①", "원문", 0.5
    )
    assert (hit.title, hit.effective_date) == ("법", date(2026, 10, 1))
