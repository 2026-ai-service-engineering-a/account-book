from __future__ import annotations

from enum import StrEnum


class SearchMode(StrEnum):
    """문서 조각을 찾는 방법. 벡터·하이브리드는 agent가 있어야 한다 — 질문을 임베딩한다."""

    KEYWORD = "keyword"
    VECTOR = "vector"
    HYBRID = "hybrid"

    @property
    def label(self) -> str:
        return _LABELS[self]


_LABELS = {
    SearchMode.KEYWORD: "낱말로(키워드)",
    SearchMode.VECTOR: "뜻으로(벡터)",
    SearchMode.HYBRID: "둘 다(하이브리드)",
}
