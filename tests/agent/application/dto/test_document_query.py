from __future__ import annotations

from agent.application.dto import DocumentQuery
from agent.domain.values import ChunkStrategy, SearchMode


def test_keyword_needs_no_vector():
    query = DocumentQuery("체력단련장", ChunkStrategy.PARAGRAPH, 5)
    assert (query.mode, query.query_vector, query.embedding_model) == (SearchMode.KEYWORD, None, "")
