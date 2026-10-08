from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agent.application.dto import Retrieval

from .chunk_body import ChunkBody


class RetrieveResponse(BaseModel):
    """찾은 조각과, 실제로 쓴 방법. 임베딩을 못 해 키워드로 물러섰으면 `fell_back`이 참이다."""

    mode: Literal["keyword", "vector", "hybrid"]
    fell_back: bool
    chunks: list[ChunkBody]

    @classmethod
    def of(cls, retrieval: Retrieval) -> RetrieveResponse:
        return cls(
            mode=retrieval.mode.value,
            fell_back=retrieval.fell_back,
            chunks=[ChunkBody.of(c) for c in retrieval.chunks],
        )
