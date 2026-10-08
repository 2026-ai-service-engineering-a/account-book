from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import ChunkStrategy, SearchMode


@dataclass(frozen=True, slots=True)
class DocumentQuery:
    """api에 묻는 문서 검색 한 번. 벡터·하이브리드면 질문 벡터와 그 모델이 실린다."""

    text: str
    strategy: ChunkStrategy
    k: int
    mode: SearchMode = SearchMode.KEYWORD
    embedding_model: str = ""
    query_vector: tuple[float, ...] | None = None
