from __future__ import annotations

from enum import StrEnum


class SearchStrategy(StrEnum):
    """검색이 어느 길로 답을 냈나(docs/ai/category-suggestion-rag.md 3장). 싼 것부터 시도한다."""

    RULE = "rule"  # 0단계 — 사용자가 만든 규칙 표
    HISTORY = "history"  # 1단계 — 같은 가맹점의 최근 이력
    VECTOR = "vector"  # 2단계 — 비슷한 텍스트의 이웃 투표
    NONE = "none"  # 근거가 없다
