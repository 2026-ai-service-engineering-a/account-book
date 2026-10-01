from __future__ import annotations

from pydantic import BaseModel

from ui.application.dto import TransactionPage
from ui.application.values import PageCursor

from .transaction_reply import TransactionReply


class TransactionPageReply(BaseModel):
    items: list[TransactionReply]
    next_cursor: str | None

    def page(self) -> TransactionPage:
        cursor = PageCursor(self.next_cursor) if self.next_cursor else None
        return TransactionPage(tuple(i.transaction() for i in self.items), cursor)
