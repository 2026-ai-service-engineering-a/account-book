from __future__ import annotations

from typing import Protocol

from api.application.dto import CategoryEvidence, IndexText
from api.domain.values import CategoryId, Direction


class CategoryIndex(Protocol):
    """카테고리 고르기의 검색 재료 — 규칙 표, 같은 텍스트의 이력, 벡터 이웃, 색인.

    거래는 쓸 때 색인 텍스트와 해시가 함께 저장된다. 벡터는 그 해시에 붙는다(4.2).
    """

    def rule_match(self, text: str, allowed: set[CategoryId]) -> CategoryId | None:
        """색인 텍스트에 패턴이 든 규칙 하나. 방향에 맞는 카테고리만."""
        ...

    def recent_with_text(
        self, text_hash: str, direction: Direction, limit: int
    ) -> tuple[CategoryEvidence, ...]:
        """같은 색인 텍스트의 최근 거래 — 최근 것부터."""
        ...

    def stored_vector(self, model: str, text_hash: str) -> tuple[float, ...] | None: ...

    def nearest(
        self,
        model: str,
        vector: tuple[float, ...],
        direction: Direction,
        allowed: set[CategoryId],
        limit: int,
    ) -> tuple[CategoryEvidence, ...]:
        """코사인 거리가 가까운 이웃. 같은 텍스트·카테고리는 하나로 세고, 대표는 최근 거래다.
        가까운 것부터, `similarity`가 채워져 있다."""
        ...

    def pending(self, model: str, limit: int) -> tuple[IndexText, ...]:
        """그 모델의 벡터가 아직 없는 색인 텍스트. 같은 텍스트는 한 번만."""
        ...

    def put_embedding(self, model: str, text_hash: str, vector: tuple[float, ...]) -> None: ...
