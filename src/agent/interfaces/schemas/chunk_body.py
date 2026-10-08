from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from agent.application.dto import RetrievedChunk


class ChunkBody(BaseModel):
    """응답의 조각 하나 — /retrieve와 /ask가 같은 모양을 쓴다. `body`는 원문이다."""

    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float

    @classmethod
    def of(cls, chunk: RetrievedChunk) -> ChunkBody:
        return cls(
            id=chunk.id,
            title=chunk.title,
            effective_date=chunk.effective_date,
            strategy=chunk.strategy.value,
            heading=chunk.heading,
            body=chunk.body,
            score=chunk.score,
        )
