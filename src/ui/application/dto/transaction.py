from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .direction import Direction
from .source import Source


@dataclass(frozen=True, slots=True)
class Transaction:
    id: str
    direction: Direction
    amount: int
    occurred_at: datetime
    category_id: str
    account_id: str
    merchant: str
    memo: str
    source: Source

    @property
    def title(self) -> str:
        """목록 한 줄의 이름. 가맹점이 없으면 메모 앞부분."""
        return self.merchant or self.memo[:20] or "(내역 없음)"
