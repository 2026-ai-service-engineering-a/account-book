from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agent.domain.values import Amount, CategoryId


@dataclass(frozen=True, slots=True)
class EvidenceLine:
    """후보의 근거가 된 과거 거래 하나."""

    merchant: str
    memo: str
    category_id: CategoryId
    amount: Amount
    day: date
