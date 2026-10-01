from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, case, cast, extract, func, select
from sqlalchemy.orm import Session

from api.application.dto import Totals, TransactionQuery
from api.domain.values import CategoryId, Money

from .rows import TransactionRow
from .transaction_filter import filter_conditions

_EXPENSE = "expense"


class SqlStatsRepository:
    """합계는 DB가 낸다. 행을 내려받아 파이썬에서 더하지 않는다."""

    def __init__(self, session: Session, zone_name: str) -> None:
        self._session = session
        # "그날"은 사용자 타임존의 날이다(development-rules 6.1)
        self._zone_name = zone_name

    def totals(self, query: TransactionQuery) -> Totals:
        expense = func.coalesce(
            func.sum(case((TransactionRow.direction == _EXPENSE, TransactionRow.amount))), 0
        )
        income = func.coalesce(
            func.sum(case((TransactionRow.direction != _EXPENSE, TransactionRow.amount))), 0
        )
        row = self._session.execute(select(expense, income).where(*filter_conditions(query))).one()
        return Totals(expense=Money(int(row[0])), income=Money(int(row[1])))

    def spent_by_category(self, start: datetime, end: datetime) -> dict[CategoryId, Money]:
        statement = (
            select(TransactionRow.category_id, func.sum(TransactionRow.amount))
            .where(
                TransactionRow.direction == _EXPENSE,
                TransactionRow.occurred_at >= start,
                TransactionRow.occurred_at < end,
            )
            .group_by(TransactionRow.category_id)
        )
        return {
            CategoryId(category): Money(int(total))
            for category, total in self._session.execute(statement)
        }

    def daily_spent(
        self, category_id: CategoryId, start: datetime, end: datetime
    ) -> list[tuple[int, Money]]:
        local = func.timezone(self._zone_name, TransactionRow.occurred_at)
        day = cast(extract("day", local), Integer)
        statement = (
            select(day, func.sum(TransactionRow.amount))
            .where(
                TransactionRow.direction == _EXPENSE,
                TransactionRow.category_id == category_id,
                TransactionRow.occurred_at >= start,
                TransactionRow.occurred_at < end,
            )
            .group_by(day)
            .order_by(day)
        )
        return [(int(d), Money(int(total))) for d, total in self._session.execute(statement)]

    def first_occurred_at(self) -> datetime | None:
        return self._session.scalar(select(func.min(TransactionRow.occurred_at)))
