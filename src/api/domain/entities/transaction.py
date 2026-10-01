from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from api.domain.values import AccountId, CategoryId, Direction, Money, Source, TransactionId


@dataclass(frozen=True, slots=True)
class Transaction:
    """거래 한 건. 시각은 aware다 — naive는 만드는 순간 죽는다(development-rules 6.1)."""

    id: TransactionId
    direction: Direction
    amount: Money
    occurred_at: datetime
    category_id: CategoryId
    account_id: AccountId
    merchant: str
    memo: str
    source: Source
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at은 aware여야 한다")
