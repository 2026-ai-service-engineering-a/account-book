from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, PositiveInt

from ui.application.dto import Direction, Source, Transaction
from ui.application.values import AccountId, CategoryId, Money, TransactionId


class TransactionReply(BaseModel):
    """api가 낸 거래 한 건. 바깥에서 온 JSON이라 받자마자 검사한다."""

    id: str
    direction: Literal["expense", "income"]
    amount: PositiveInt
    occurred_at: AwareDatetime
    category_id: str
    account_id: str
    merchant: str
    memo: str
    source: Literal["manual", "agent", "import"]

    def transaction(self) -> Transaction:
        return Transaction(
            id=TransactionId(self.id),
            direction=Direction(self.direction),
            amount=Money(self.amount),
            occurred_at=self.occurred_at,
            category_id=CategoryId(self.category_id),
            account_id=AccountId(self.account_id),
            merchant=self.merchant,
            memo=self.memo,
            source=Source(self.source),
        )
