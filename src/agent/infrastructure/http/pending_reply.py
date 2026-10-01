from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel

from agent.application.dto import PendingText


class _PendingItem(TypedDict):
    text_hash: str
    text: str


class PendingReply(BaseModel):
    """api `GET /v1/embeddings/pending`의 응답 본문."""

    items: list[_PendingItem]

    def texts(self) -> tuple[PendingText, ...]:
        return tuple(PendingText(i["text_hash"], i["text"]) for i in self.items)
