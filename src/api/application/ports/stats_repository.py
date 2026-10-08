from __future__ import annotations

from datetime import datetime
from typing import Protocol

from api.application.dto import Frequency, Totals, TransactionQuery
from api.domain.values import CategoryId, Money


class StatsRepository(Protocol):
    """집계는 DB가 한다. 거래 목록을 내려받아 더하지 않는다(api-contract 6장)."""

    def totals(self, query: TransactionQuery) -> Totals:
        """걸름에 맞는 거래의 지출 합과 수입 합. 쪽 나누기(cursor·limit)는 보지 않는다."""
        ...

    def frequency(self, query: TransactionQuery) -> Frequency:
        """걸름에 맞는 거래의 건수·날 수·평균 간격·회당 평균. `totals`와 같은 걸름이다."""
        ...

    def spent_by_category(self, start: datetime, end: datetime) -> dict[CategoryId, Money]:
        """기간 안 지출을 카테고리별로. 쓴 게 없는 카테고리는 없다."""
        ...

    def daily_spent(
        self, category_id: CategoryId, start: datetime, end: datetime
    ) -> list[tuple[int, Money]]:
        """기간 안 지출을 사용자 타임존의 날(1~31)별로."""
        ...

    def first_occurred_at(self) -> datetime | None: ...
