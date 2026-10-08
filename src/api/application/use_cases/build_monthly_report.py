from __future__ import annotations

from collections.abc import Callable
from datetime import tzinfo

from api.application.dto import CategoryChange, MonthlyReport, MonthTotal, TransactionQuery
from api.application.ports import Clock, UnitOfWork
from api.domain.rules import change
from api.domain.values import CategoryId, Direction, Money, Period

# 추세 차트에 보이는 달 수
_TREND_MONTHS = 6


class BuildMonthlyReport:
    """월간 리포트 — 합계, 지난달 대비, 카테고리별 증감, 최근 여섯 달(ui_docs/pages/reports.md).

    첫 기록이 있는 달보다 앞이면 비교하지 않는다. "지난달 0원"은 비교가 아니라 기록이 없던 것이다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def __call__(self, period: Period) -> MonthlyReport:
        now = self._clock.now()
        zone = now.tzinfo
        if zone is None:
            raise RuntimeError("Clock은 aware 시각을 내야 한다")
        with self._unit_of_work() as uow:
            first_at = uow.stats.first_occurred_at()
            first = Period.of(first_at.astimezone(zone).date()) if first_at else None
            has_previous = first is not None and first < period
            this_start, this_end = period.bounds(zone)
            prev_start, prev_end = period.previous().bounds(zone)
            this_spent = uow.stats.spent_by_category(this_start, this_end)
            prev_spent = uow.stats.spent_by_category(prev_start, prev_end) if has_previous else None
            changes = _changes(uow, this_spent, prev_spent)
            totals = uow.stats.totals(TransactionQuery(start=this_start, end=this_end))
            previous = (
                uow.stats.totals(TransactionQuery(start=prev_start, end=prev_end))
                if has_previous
                else None
            )
            months = _months(uow, period, first, zone)
        return MonthlyReport(
            period=period,
            totals=totals,
            previous=previous,
            by_category=changes,
            months=months,
            through_day=now.day if Period.of(now.date()) == period else None,
        )


def _changes(
    uow: UnitOfWork,
    this_spent: dict[CategoryId, Money],
    prev_spent: dict[CategoryId, Money] | None,
) -> tuple[CategoryChange, ...]:
    changes = []
    for category in uow.catalog.categories(Direction.EXPENSE):
        now = this_spent.get(category.id, Money(0))
        before = prev_spent.get(category.id, Money(0)) if prev_spent is not None else None
        if not now.amount and not (before and before.amount):
            continue
        delta = None if before is None else now - before
        percent = None if before is None else change.percent(before, now)
        changes.append(CategoryChange(category, now, before, delta, percent))
    return tuple(sorted(changes, key=lambda c: c.this_month, reverse=True))


def _months(
    uow: UnitOfWork, period: Period, first: Period | None, zone: tzinfo
) -> tuple[MonthTotal, ...]:
    out: list[MonthTotal] = []
    cursor = period
    for _ in range(_TREND_MONTHS):
        if first is None or cursor < first:
            break
        start, end = cursor.bounds(zone)
        totals = uow.stats.totals(TransactionQuery(start=start, end=end))
        out.append(MonthTotal(cursor, totals.expense, totals.income))
        cursor = cursor.previous()
    return tuple(reversed(out))
