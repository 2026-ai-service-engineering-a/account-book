from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from api.domain.values import AccountId, CategoryId, Direction, Money


@dataclass(frozen=True, slots=True)
class TransactionDraft:
    """새로 넣거나 고칠 거래의 값. 검사 전이다 — 규칙은 `check_draft`가 본다."""

    direction: Direction
    amount: Money
    occurred_at: datetime
    category_id: CategoryId
    account_id: AccountId
    merchant: str = ""
    memo: str = ""
