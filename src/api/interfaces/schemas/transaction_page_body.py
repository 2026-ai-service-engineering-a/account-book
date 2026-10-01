from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import TransactionPage

from .transaction_body import TransactionBody


class TransactionPageBody(BaseModel):
    """목록 한 쪽. `next_cursor`가 없으면 마지막 쪽이다 — 커서는 풀어 보지 않는다."""

    items: list[TransactionBody]
    next_cursor: str | None

    @classmethod
    def of(cls, page: TransactionPage) -> TransactionPageBody:
        return cls(items=[TransactionBody.of(t) for t in page.items], next_cursor=page.next_cursor)
