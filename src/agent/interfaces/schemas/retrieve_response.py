from __future__ import annotations

from datetime import date
from typing import Literal, TypedDict

from pydantic import BaseModel

from agent.application.dto import Retrieval, RetrievedChunk


class _Chunk(TypedDict):
    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float


class RetrieveResponse(BaseModel):
    """찾은 조각과, 실제로 쓴 방법. 임베딩을 못 해 키워드로 물러섰으면 `fell_back`이 참이다.

    조각의 모양(_Chunk)은 이 응답만 쓴다(development-rules 1.2의 예외).
    """

    mode: Literal["keyword", "vector", "hybrid"]
    fell_back: bool
    chunks: list[_Chunk]

    @classmethod
    def of(cls, retrieval: Retrieval) -> RetrieveResponse:
        return cls(
            mode=retrieval.mode.value,
            fell_back=retrieval.fell_back,
            chunks=[_chunk(c) for c in retrieval.chunks],
        )


def _chunk(chunk: RetrievedChunk) -> _Chunk:
    return {
        "id": chunk.id,
        "title": chunk.title,
        "effective_date": chunk.effective_date,
        "strategy": chunk.strategy.value,
        "heading": chunk.heading,
        "body": chunk.body,
        "score": chunk.score,
    }
