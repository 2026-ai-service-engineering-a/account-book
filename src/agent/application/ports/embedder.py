from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    """텍스트를 벡터로. 임베딩도 LLM 제공자 호출이라 agent만 한다(category-suggestion-rag 4.3)."""

    @property
    def model(self) -> str:
        """벡터가 어느 모델 것인지. 모델을 바꾸면 api가 전부 다시 색인할 것으로 본다."""
        ...

    async def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """넣은 순서대로 벡터 하나씩. 닿지 못하면 `ModelUnavailable`."""
        ...
