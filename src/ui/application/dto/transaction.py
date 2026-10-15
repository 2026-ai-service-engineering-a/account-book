from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ui.application.values import AccountId, CategoryId, Money, RunId, TransactionId

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
    run_id: RunId | None = None  # agent가 넣었으면 그 실행 — 실행 기록으로 잇는다

    @property
    def title(self) -> str:
        """목록 한 줄의 이름. 가맹점이 없으면 메모 앞부분."""
        return self.merchant or self.memo[:20] or "(내역 없음)"
