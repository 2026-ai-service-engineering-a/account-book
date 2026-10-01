from __future__ import annotations

from typing import Protocol

from ui.application.dto import CategoryQuery, CategorySearch, IndexText
from ui.application.values import TextHash


class CategoryIndex(Protocol):
    """카테고리 고르기의 검색 쪽 — api의 `/v1/categories/suggest`와 색인(embeddings) 엔드포인트.

    검색은 api, 판단은 agent다(docs/ai/category-suggestion-rag.md 2장). api가 없는 동안에는
    메모리 대역이 서고, ui가 이 포트를 HTTP로 열어 agent가 부르게 한다.
    """

    async def suggest(self, query: CategoryQuery) -> CategorySearch: ...

    async def pending(self, embedding_model: str, limit: int) -> tuple[IndexText, ...]:
        """그 모델의 벡터가 아직 없는 색인 텍스트. 같은 텍스트는 한 번만 낸다."""
        ...

    async def put_embedding(
        self, text_hash: TextHash, embedding_model: str, vector: tuple[float, ...]
    ) -> None: ...
