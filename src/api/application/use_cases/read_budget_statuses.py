from __future__ import annotations

from collections.abc import Callable

from api.application.dto import BudgetStatus
from api.application.ports import Clock, UnitOfWork
from api.domain.entities import Category
from api.domain.rules import budget_pace
from api.domain.values import CategoryId, Direction, Money, Period


class ReadBudgetStatuses:
    """예산 대비 소진율과 페이스 — `get_budget_status` 도구의 자리. 지출 카테고리 전부를 낸다.

    예산을 정하지 않은 카테고리도 들어 있다(쓴 돈만 있고 나머지는 비어 있다).
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def __call__(
        self, period: Period, category_id: CategoryId | None = None
    ) -> tuple[BudgetStatus, ...]:
        with self._unit_of_work() as uow:
            return statuses(uow, self._clock, period, category_id)


def statuses(
    uow: UnitOfWork, clock: Clock, period: Period, category_id: CategoryId | None = None
) -> tuple[BudgetStatus, ...]:
    """작업 단위 안에서 계산한다. 예산을 정한 직후(SetBudget)도 같은 트랜잭션에서 읽는다."""
    now = clock.now()
    zone = now.tzinfo
    if zone is None:
        raise RuntimeError("Clock은 aware 시각을 내야 한다")
    start, end = period.bounds(zone)
    limits = uow.budgets.limits(period)
    spent = uow.stats.spent_by_category(start, end)
    through = budget_pace.elapsed_days(period, now.date())
    out = []
    for category in uow.catalog.categories(Direction.EXPENSE):
        if category_id is not None and category.id != category_id:
            continue
        used = spent.get(category.id, Money(0))
        limit = limits.get(category.id)
        if limit is None:
            out.append(BudgetStatus(category, None, used, None, None, None, None))
            continue
        days = uow.stats.daily_spent(category.id, start, end)
        out.append(_with_limit(category, limit, used, period, through, days))
    return tuple(out)


def _with_limit(
    category: Category,
    limit: Money,
    used: Money,
    period: Period,
    through: int,
    days: list[tuple[int, Money]],
) -> BudgetStatus:
    series = budget_pace.cumulative(days, through)
    over = budget_pace.crossing_day(series, limit, period.days)
    return BudgetStatus(
        category=category,
        limit=limit,
        spent=used,
        remaining=limit - used,
        percent=used.amount * 100 // limit.amount,
        projected=budget_pace.project(used, through, period.days),
        over_on=budget_pace.day_in(period, over),
    )
