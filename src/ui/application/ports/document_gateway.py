from __future__ import annotations

from typing import Protocol

from ui.application.dto import ChunkStrategy, DocumentResults, SearchMode


class DocumentGateway(Protocol):
    """문서 조각 찾기(docs/ai/document-rag.md). 지금은 키워드 — api의 `/v1/documents/search`."""

    async def search(
        self,
        query: str,
        strategy: ChunkStrategy,
        k: int | None = None,
        mode: SearchMode = SearchMode.KEYWORD,
    ) -> DocumentResults:
        """점수 높은 순으로 k개 — 비우면 찾는 쪽의 기본(agent는 DOC_TOP_K, 아니면 5).

        점수로 거르지 않는다. 고른 방법을 못 쓰면 낱말로 찾고 밝힌다.
        """
        ...
