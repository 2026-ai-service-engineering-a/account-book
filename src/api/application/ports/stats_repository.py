from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from api.application.dto import CategoryBaseline, Frequency, Totals, TransactionQuery
from api.domain.entities import Transaction
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

    def baselines(self, query: TransactionQuery, since: datetime) -> tuple[CategoryBaseline, ...]:
        """걸름에 맞는 거래가 있는 카테고리마다 평소. 기준은 `[since, query.start)`의 같은 방향
        거래 전부다 — 걸름의 카테고리·글자는 판정할 거래를 고를 뿐 평소를 좁히지 않는다."""
        ...

    def above(
        self, query: TransactionQuery, uppers: Mapping[CategoryId, Money], limit: int
    ) -> tuple[Transaction, ...]:
        """걸름에 맞고 카테고리의 한계를 넘은 거래. 한계 대비 금액이 큰 순서로 `limit`건까지."""
        ...
