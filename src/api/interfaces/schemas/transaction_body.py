from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel

from api.domain.entities import Transaction


class TransactionBody(BaseModel):
    """응답의 거래 한 건. 도메인 객체를 그대로 내보내지 않는다(development-rules 5.5)."""

    id: str
    direction: Literal["expense", "income"]
    amount: int
    occurred_at: AwareDatetime
    category_id: str
    account_id: str
    merchant: str
    memo: str
    source: Literal["manual", "agent", "import"]
    run_id: str | None

    @classmethod
    def of(cls, transaction: Transaction) -> TransactionBody:
        return cls(
            id=transaction.id,
            direction=transaction.direction.value,
            amount=transaction.amount.amount,
            occurred_at=transaction.occurred_at,
            category_id=transaction.category_id,
            account_id=transaction.account_id,
            merchant=transaction.merchant,
            memo=transaction.memo,
            source=transaction.source.value,
            run_id=transaction.run_id,
        )
