from __future__ import annotations

from enum import StrEnum


class SearchMode(StrEnum):
    """문서 조각을 찾는 방법(docs/ai/document-rag.md 7.2). 벡터·하이브리드는 질문을 임베딩한다."""

    KEYWORD = "keyword"
    VECTOR = "vector"
    HYBRID = "hybrid"
