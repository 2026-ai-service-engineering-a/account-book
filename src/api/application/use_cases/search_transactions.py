from __future__ import annotations

from collections.abc import Callable
from datetime import tzinfo

from api.application.dto import TransactionPage, TransactionQuery
from api.application.ports import UnitOfWork
from api.domain.rules import period_bounds
from api.domain.values import CategoryId, Direction, Period, TimeRange

# 목록은 언제나 페이지로 낸다. 에이전트가 3년치를 통째로 받아 가지 못하게(api-contract 6장)
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class SearchTransactions:
    """거래 목록. 기간은 사용자 타임존의 달로 받아 여기서 UTC 경계로 푼다(development-rules 6.1)."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], zone: tzinfo) -> None:
        self._unit_of_work = unit_of_work
        self._zone = zone

    def __call__(
        self,
        period: Period | TimeRange | None = None,
        direction: Direction | None = None,
        category_id: CategoryId | None = None,
        text: str = "",
        cursor: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> TransactionPage:
        start, end = period_bounds.bounds(period, self._zone)
        query = TransactionQuery(
            start=start,
            end=end,
            direction=direction,
            category_id=category_id,
            text=text.strip(),
            cursor=cursor,
            limit=max(1, min(limit, MAX_LIMIT)),
        )
        with self._unit_of_work() as uow:
            return uow.transactions.search(query)
