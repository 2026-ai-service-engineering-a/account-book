from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agent.application.dto import DocumentAnswer

from .chunk_body import ChunkBody


class AskResponse(BaseModel):
    """문서 Q&A의 답. 어떤 끝이든 `chunks`(찾은 조각 전부)가 있다 — 화면이 원문을 보인다.

    - answered: `answer`와 그 근거 `citations`.
    - abstained: 조문에 근거가 없다. `reason`에 한 줄.
    - search_only: 답을 만들거나 검증하지 못했다. 찾은 조각만.
    """

    status: Literal["answered", "abstained", "search_only"]
    answer: str
    citations: list[ChunkBody]
    chunks: list[ChunkBody]
    reason: str
    mode: Literal["keyword", "vector", "hybrid"]
    fell_back: bool

    @classmethod
    def of(cls, found: DocumentAnswer) -> AskResponse:
        return cls(
            status=found.status.value,
            answer=found.answer,
            citations=[ChunkBody.of(c) for c in found.citations],
            chunks=[ChunkBody.of(c) for c in found.chunks],
            reason=found.reason,
            mode=found.retrieval.mode.value,
            fell_back=found.retrieval.fell_back,
        )
