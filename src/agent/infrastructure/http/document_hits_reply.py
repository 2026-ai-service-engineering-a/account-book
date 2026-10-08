from __future__ import annotations

from datetime import date
from typing import Literal, TypedDict

from pydantic import RootModel

from agent.application.dto import RetrievedChunk
from agent.domain.values import ChunkStrategy


class _Hit(TypedDict):
    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float


class DocumentHitsReply(RootModel[list[_Hit]]):
    """api `POST /v1/documents/search`의 응답 본문 — 점수 높은 순의 조각."""

    def chunks(self) -> tuple[RetrievedChunk, ...]:
        return tuple(
            RetrievedChunk(
                id=h["id"],
                title=h["title"],
                effective_date=h["effective_date"],
                strategy=ChunkStrategy(h["strategy"]),
                heading=h["heading"],
                body=h["body"],
                score=h["score"],
            )
            for h in self.root
        )
