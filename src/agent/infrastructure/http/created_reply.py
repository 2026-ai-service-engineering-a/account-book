from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, PositiveInt

from agent.domain.tools import TransactionLine
from agent.domain.values import Amount, CategoryId, Direction


class CreatedReply(BaseModel):
    """api `POST /v1/transactions`의 201 본문. 기록한 거래 한 줄만 읽는다."""

    id: str
    direction: Literal["expense", "income"]
    amount: PositiveInt
    occurred_at: AwareDatetime
    category_id: str
    merchant: str
    memo: str

    def line(self) -> TransactionLine:
        return TransactionLine(
            id=self.id,
            occurred_at=self.occurred_at,
            direction=Direction(self.direction),
            amount=Amount(self.amount),
            category_id=CategoryId(self.category_id),
            merchant=self.merchant,
            memo=self.memo,
        )
