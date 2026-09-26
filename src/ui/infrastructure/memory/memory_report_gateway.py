from __future__ import annotations

from ui.application.dto import (
    CategoryChange,
    Direction,
    MonthlyReport,
    MonthTotal,
    PaceSeries,
    Period,
    Totals,
    Transaction,
    TransactionFilter,
)
from ui.application.ports import Clock
from ui.application.values import CategoryId, Money

from . import pace_math
from .memory_store import MemoryStore

_TREND_MONTHS = 6


class MemoryReportGateway:
    """`/v1/summary`의 대역. 합계는 여기서만 낸다."""

    def __init__(self, store: MemoryStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    async def totals(self, criteria: TransactionFilter) -> Totals:
        return self._sum(self._store.matching(criteria))

    async def monthly(self, period: Period) -> MonthlyReport:
        first = self._first_period()
        has_previous = first is not None and first < period
        this_rows = self._store.matching(TransactionFilter(period))
        prev_rows = self._store.matching(TransactionFilter(period.previous()))
        today = self._clock.now().date()
        return MonthlyReport(
            period=period,
            totals=self._sum(this_rows),
            previous=self._sum(prev_rows) if has_previous else None,
            by_category=self._changes(this_rows, prev_rows if has_previous else None),
            months=self._months(period, first),
            through_day=today.day if Period.of(today) == period else None,
        )

    async def pace(self, category_id: CategoryId, period: Period) -> PaceSeries | None:
        limit = self._store.limits.get(category_id)
        category = self._store.categories.get(category_id)
        through = pace_math.elapsed_days(period, self._clock.now().date())
        if limit is None or category is None or through == 0:
            return None
        rows = self._store.matching(TransactionFilter(period, Direction.EXPENSE, category_id))
        series = pace_math.cumulative(
            ((self._store.local_day(t).day, t.amount) for t in rows), through
        )
        spent = series[-1] if series else Money(0)
        over_day = pace_math.crossing_day(series, limit, period.days)
        return PaceSeries(
            category=category,
            limit=limit,
            cumulative=series,
            days_in_month=period.days,
            projected=pace_math.project(spent, through, period.days),
            over_on=pace_math.day_in(period, over_day),
        )

    def _first_period(self) -> Period | None:
        days = [self._store.local_day(t) for t in self._store.transactions.values()]
        return Period.of(min(days)) if days else None

    def _changes(
        self, this_rows: list[Transaction], prev_rows: list[Transaction] | None
    ) -> tuple[CategoryChange, ...]:
        changes = []
        for category in self._store.categories.values():
            if category.direction != Direction.EXPENSE:
                continue
            now = _spent(this_rows, category.id)
            before = _spent(prev_rows, category.id) if prev_rows is not None else None
            if not now and not before:
                continue
            delta = None if before is None else now - before
            percent = (
                round(abs(delta.amount) * 100 / before.amount)
                if delta is not None and before
                else None
            )
            changes.append(CategoryChange(category, now, before, delta, percent))
        return tuple(sorted(changes, key=lambda c: c.this_month, reverse=True))

    def _months(self, period: Period, first: Period | None) -> tuple[MonthTotal, ...]:
        out: list[MonthTotal] = []
        cursor = period
        for _ in range(_TREND_MONTHS):
            if first is None or cursor < first:
                break
            totals = self._sum(self._store.matching(TransactionFilter(cursor)))
            out.append(MonthTotal(cursor, totals.expense, totals.income))
            cursor = cursor.previous()
        return tuple(reversed(out))

    @staticmethod
    def _sum(rows: list[Transaction]) -> Totals:
        return Totals(
            expense=Money.total(t.amount for t in rows if t.direction == Direction.EXPENSE),
            income=Money.total(t.amount for t in rows if t.direction == Direction.INCOME),
        )


def _spent(rows: list[Transaction] | None, category_id: CategoryId) -> Money:
    return Money.total(t.amount for t in rows or () if t.category_id == category_id)
