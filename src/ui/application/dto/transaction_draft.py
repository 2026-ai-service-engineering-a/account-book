from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ui.application.values import AccountId, CategoryId, Money

from .direction import Direction


@dataclass(frozen=True, slots=True)
class TransactionDraft:
    """저장하기 전의 거래. 폼과 확인 카드가 같은 모양을 쓴다."""

    direction: Direction
    amount: Money
    occurred_at: datetime  # aware
    category_id: CategoryId
    account_id: AccountId
    merchant: str = ""
    memo: str = ""
