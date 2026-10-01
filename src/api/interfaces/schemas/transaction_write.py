from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, StrictInt

from api.application.dto import TransactionDraft
from api.domain.values import AccountId, CategoryId, Direction, Money


class TransactionWrite(BaseModel):
    """POST·PATCH의 본문 — 거래의 값 전부. 금액은 정수 원이다("8,500원" 같은 글자는 받지 않는다).

    여기서는 모양만 본다. 카테고리가 있는지, 방향에 맞는지는 유스케이스가 본다.
    """

    direction: Literal["expense", "income"]
    amount: StrictInt
    occurred_at: AwareDatetime
    category_id: str = Field(min_length=1, max_length=32)
    account_id: str = Field(min_length=1, max_length=32)
    merchant: str = ""
    memo: str = ""

    def draft(self) -> TransactionDraft:
        return TransactionDraft(
            direction=Direction(self.direction),
            amount=Money(self.amount),
            occurred_at=self.occurred_at,
            category_id=CategoryId(self.category_id),
            account_id=AccountId(self.account_id),
            merchant=self.merchant,
            memo=self.memo,
        )
