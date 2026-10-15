from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    case,
    cast,
    distinct,
    extract,
    func,
    select,
    type_coerce,
)
from sqlalchemy.orm import Session

from api.application.dto import CategoryBaseline, Frequency, Totals, TransactionQuery
from api.domain.entities import Transaction
from api.domain.values import CategoryId, Money

from .rows import TransactionRow
from .sql_transaction_repository import transaction_of
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

    def frequency(self, query: TransactionQuery) -> Frequency:
        # 날은 사용자 타임존의 날이다. 자정 넘어 긁은 카드는 다음 날로 센다
        day = cast(func.timezone(self._zone_name, TransactionRow.occurred_at), Date)
        day_count = func.count(distinct(day))
        # 거래가 있던 날 사이의 평균 간격 — 같은 날 여러 건이 간격을 줄이지 않게 날로 잰다
        span = cast(func.max(day) - func.min(day), Numeric)
        gap = func.round(span / func.nullif(day_count - 1, 0), 1)
        average = func.round(func.avg(TransactionRow.amount))
        row = self._session.execute(
            select(func.count(), day_count, gap, average).where(*filter_conditions(query))
        ).one()
        return Frequency(
            count=int(row[0]),
            day_count=int(row[1]),
            avg_gap_days=float(row[2]) if row[2] is not None else None,
            avg_amount=Money(int(row[3])) if row[3] is not None else None,
        )

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

    def baselines(self, query: TransactionQuery, since: datetime) -> tuple[CategoryBaseline, ...]:
        if query.start is None or query.direction is None:
            raise ValueError("평소는 기간의 시작과 방향이 있어야 잰다")
        t = TransactionRow
        same_way = t.direction == query.direction.value
        present = select(t.category_id).where(*filter_conditions(query)).distinct().cte("present")
        history = (
            select(t.category_id, func.min(t.occurred_at).label("first_at"))
            .where(same_way, t.occurred_at < query.start)
            .group_by(t.category_id)
            .cte("history")
        )
        window = (
            select(t.category_id, t.amount)
            .where(same_way, t.occurred_at >= since, t.occurred_at < query.start)
            .cte("window")
        )
        # 중앙값은 percentile_cont다 — 짝수 건이면 가운데 둘의 평균. 원 단위로 반올림한다
        middle = (
            select(
                window.c.category_id,
                func.percentile_cont(0.5).within_group(window.c.amount).label("median"),
                func.count().label("n"),
            )
            .group_by(window.c.category_id)
            .cte("middle")
        )
        distance = func.abs(window.c.amount - middle.c.median)
        spread = (
            select(
                window.c.category_id,
                func.percentile_cont(0.5).within_group(distance).label("mad"),
            )
            .join(middle, middle.c.category_id == window.c.category_id)
            .group_by(window.c.category_id)
            .cte("spread")
        )
        # CTE의 칸은 타입을 잃는다. 내보낼 때 다시 붙인다
        statement = (
            select(
                type_coerce(present.c.category_id, String),
                cast(func.round(cast(middle.c.median, Numeric)), Integer),
                cast(func.round(cast(spread.c.mad, Numeric)), Integer),
                cast(middle.c.n, Integer),
                type_coerce(history.c.first_at, DateTime(timezone=True)),
            )
            .outerjoin(history, history.c.category_id == present.c.category_id)
            .outerjoin(middle, middle.c.category_id == present.c.category_id)
            .outerjoin(spread, spread.c.category_id == present.c.category_id)
            .order_by(present.c.category_id)
        )
        return tuple(
            CategoryBaseline(
                category_id=CategoryId(category),
                median=Money(median or 0),
                mad=Money(mad or 0),
                count=n or 0,
                first_at=first_at,
            )
            for category, median, mad, n, first_at in self._session.execute(statement)
        )

    def above(
        self, query: TransactionQuery, uppers: Mapping[CategoryId, Money], limit: int
    ) -> tuple[Transaction, ...]:
        if not uppers:
            return ()
        t = TransactionRow
        upper = case({c: u.amount for c, u in uppers.items()}, value=t.category_id)
        statement = (
            select(t)
            .where(*filter_conditions(query), t.category_id.in_(uppers), t.amount > upper)
            # 한계를 많이 넘은 것부터. 금액이 아니라 비율이다 — 카테고리마다 평소가 다르다
            .order_by((cast(t.amount, Numeric) / upper).desc(), t.occurred_at.desc(), t.id)
            .limit(limit)
        )
        return tuple(transaction_of(row) for row in self._session.scalars(statement))
