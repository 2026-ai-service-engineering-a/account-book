from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ui.application.dto import Direction, TransactionDraft
from ui.infrastructure.memory import MemoryStore

SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 9, 17, 18, 0, tzinfo=SEOUL)


class FixedClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore.create(SEOUL)


def draft(
    amount: int = 8_500,
    day: int = 16,
    category: str = "food",
    merchant: str = "김밥천국",
    direction: Direction = Direction.EXPENSE,
    month: int = 9,
) -> TransactionDraft:
    return TransactionDraft(
        direction=direction,
        amount=amount,
        occurred_at=datetime(2026, month, day, 12, 30, tzinfo=SEOUL),
        category_id=category,
        account_id="card",
        merchant=merchant,
    )
