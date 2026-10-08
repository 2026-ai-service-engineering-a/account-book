from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from api.application.dto import ChunkHit
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
