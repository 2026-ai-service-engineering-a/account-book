from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from api.application.dto import ChunkHit, IndexText
from api.domain.entities import Document, DocumentChunk
from api.domain.values import ChunkStrategy


class DocumentRepository(Protocol):
    """문서와 그 조각. 조각은 청킹 전략마다 따로 있다(docs/ai/document-rag.md 7.2)."""

    def replace(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        """문서를 넣거나 바꾸고, 그 문서의 조각을 통째로 갈아 끼운다. 몇 번을 해도 같다."""
        ...

    def search(self, query: str, strategy: ChunkStrategy, k: int) -> tuple[ChunkHit, ...]:
        """한 전략의 조각 중 키워드가 가장 비슷한 k개, 점수 높은 순. 임계값으로 거르지 않는다."""
        ...

    def pending(self, model: str, limit: int) -> tuple[IndexText, ...]:
        """그 모델의 벡터가 아직 없는 조각의 찾는 글. 같은 글은 하나로 — 해시가 같다."""
        ...

    def nearest(
        self, vector: tuple[float, ...], model: str, strategy: ChunkStrategy, k: int
    ) -> tuple[ChunkHit, ...]:
        """한 전략의 조각 중 질문 벡터와 코사인이 가장 가까운 k개. 그 모델의 벡터가 있는 조각만."""
        ...
