from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent.domain.values import CategoryId, Direction, Money, PaymentMethod


@dataclass(frozen=True, slots=True)
class CreateTransactionInput:
    """거래 한 건의 칸. 이 도구는 두 박자다 — 제안이 먼저고, 사람이 확인해야 api에 간다
    (ai/tools.md 7장). 그래서 `dry_run` 같은 인자가 없다. 제안은 인자가 아니라 흐름의 단계다.
    """

    direction: Direction
    amount: Money
    occurred_at: datetime  # aware
    category_id: CategoryId
    account: PaymentMethod
    merchant: str = ""
    memo: str = ""

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at은 aware여야 한다")
