from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from api.application.dto import ChunkHit


class ChunkHitBody(BaseModel):
    """검색이 찾은 조각 하나. `body`는 원문 — 화면은 이것을 인용으로 보인다."""

    id: str
    document_id: str
    title: str  # 법령명
    effective_date: date  # 시행일자 — 인용 아래에 늘 붙인다
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float

    @classmethod
    def of(cls, hit: ChunkHit) -> ChunkHitBody:
        return cls(
            id=hit.chunk.id,
            document_id=hit.chunk.document_id,
            title=hit.title,
            effective_date=hit.effective_date,
            strategy=hit.chunk.strategy.value,
            heading=hit.chunk.heading,
            body=hit.chunk.body,
            score=round(hit.score, 4),
        )
