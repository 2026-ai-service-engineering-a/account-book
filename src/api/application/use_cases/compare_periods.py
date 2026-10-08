from __future__ import annotations

from collections.abc import Callable

from api.application.dto import PeriodChange
from api.application.ports import UnitOfWork
from api.domain.rules import change
from api.domain.values import CategoryId, Direction, Money, TimeRange


class ComparePeriods:
    """두 기간의 카테고리별 지출 합과 증감 — `compare_periods` 도구의 자리(api-contract 6장).

    지출만 본다. 월간 리포트의 카테고리별 증감과 같은 표다. 두 기간 모두 0인 카테고리는
    빼지만, `category_id`로 콕 집어 물었으면 0이어도 한 줄을 낸다 — "안 썼다"도 답이다.

    "지난달보다 늘었나"를 같은 날까지로 견줄지는 부르는 쪽이 기간을 잘라서 정한다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self, a: TimeRange, b: TimeRange, category_id: CategoryId | None = None
    ) -> tuple[PeriodChange, ...]:
        with self._unit_of_work() as uow:
            categories = [
                c
                for c in uow.catalog.categories(Direction.EXPENSE)
                if category_id is None or c.id == category_id
            ]
            spent_a = uow.stats.spent_by_category(a.start, a.end)
            spent_b = uow.stats.spent_by_category(b.start, b.end)
        changes = []
        for category in categories:
            before = spent_a.get(category.id, Money(0))
            after = spent_b.get(category.id, Money(0))
            if category_id is None and not before.amount and not after.amount:
                continue
            changes.append(
                PeriodChange(category, before, after, after - before, change.percent(before, after))
            )
        return tuple(sorted(changes, key=lambda c: c.b, reverse=True))
