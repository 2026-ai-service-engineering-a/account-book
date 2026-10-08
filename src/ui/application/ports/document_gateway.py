from __future__ import annotations

from typing import Protocol

from ui.application.dto import ChunkStrategy, DocumentHit


class DocumentGateway(Protocol):
    """문서 조각 찾기(docs/ai/document-rag.md). 지금은 키워드 — api의 `/v1/documents/search`."""

    async def search(
        self, query: str, strategy: ChunkStrategy, k: int = 5
    ) -> tuple[DocumentHit, ...]:
        """점수 높은 순으로 k개. 점수로 거르지 않는다."""
        ...
