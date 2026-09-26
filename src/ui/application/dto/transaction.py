from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ui.application.values import AccountId, CategoryId, Money, TransactionId

from .direction import Direction
from .source import Source


@dataclass(frozen=True, slots=True)
class Transaction:
    id: TransactionId
    direction: Direction
    amount: Money
    occurred_at: datetime
    category_id: CategoryId
    account_id: AccountId
    merchant: str
    memo: str
    source: Source

    @property
    def title(self) -> str:
        """목록 한 줄의 이름. 가맹점이 없으면 메모 앞부분."""
        return self.merchant or self.memo[:20] or "(내역 없음)"
