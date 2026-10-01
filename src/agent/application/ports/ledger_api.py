from __future__ import annotations

from typing import Protocol

from agent.application.dto import CategoryQuery, PendingText, SearchResult


class LedgerApi(Protocol):
    """agent가 보는 api. DB는 모른다 — 벡터 검색조차 이 엔드포인트를 지난다(docs/ai/README.md 3장).

    닿지 못하면 `LedgerUnavailable`.
    """

    async def suggest(self, query: CategoryQuery) -> SearchResult: ...

    async def pending(self, embedding_model: str, limit: int) -> tuple[PendingText, ...]: ...

    async def put_embedding(
        self, text_hash: str, embedding_model: str, vector: tuple[float, ...]
    ) -> None: ...
