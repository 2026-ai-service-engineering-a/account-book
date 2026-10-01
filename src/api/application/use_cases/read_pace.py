from __future__ import annotations

from collections.abc import Callable

from api.application.dto import PaceSeries
from api.application.ports import Clock, UnitOfWork
from api.domain.rules import budget_pace
from api.domain.values import CategoryId, Direction, Money, Period


class ReadPace:
    """한 카테고리의 날짜별 누적 지출과 페이스. 예산이 없거나 아직 오지 않은 달이면 None."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def __call__(self, category_id: CategoryId, period: Period) -> PaceSeries | None:
        now = self._clock.now()
        zone = now.tzinfo
        if zone is None:
            raise RuntimeError("Clock은 aware 시각을 내야 한다")
        through = budget_pace.elapsed_days(period, now.date())
        with self._unit_of_work() as uow:
            category = next(
                (c for c in uow.catalog.categories(Direction.EXPENSE) if c.id == category_id),
                None,
            )
            limit = uow.budgets.limits(period).get(category_id)
            if category is None or limit is None or through == 0:
                return None
            start, end = period.bounds(zone)
            series = budget_pace.cumulative(uow.stats.daily_spent(category_id, start, end), through)
        spent = series[-1] if series else Money(0)
        return PaceSeries(
            category=category,
            limit=limit,
            cumulative=series,
            days_in_month=period.days,
            projected=budget_pace.project(spent, through, period.days),
            over_on=budget_pace.day_in(
                period, budget_pace.crossing_day(series, limit, period.days)
            ),
        )
