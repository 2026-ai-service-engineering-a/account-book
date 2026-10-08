from __future__ import annotations

from enum import StrEnum


class SearchMode(StrEnum):
    """문서 조각을 찾는 방법. 셋을 다 두고 재서 고른다(docs/ai/document-rag.md 7.2)."""

    KEYWORD = "keyword"  # pg_trgm — 낱말이 겹치는가
    VECTOR = "vector"  # 질문 벡터와 조각 벡터의 코사인 — 뜻이 가까운가
    HYBRID = "hybrid"  # 두 순위를 RRF로 합친다. 점수는 더하지 않는다
