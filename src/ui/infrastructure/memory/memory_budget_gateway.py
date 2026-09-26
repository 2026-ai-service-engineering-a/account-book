from __future__ import annotations

from ui.application.dto import BudgetStatus, Category, Direction, Period, TransactionFilter
from ui.application.errors import LedgerValidationError
from ui.application.ports import Clock
from ui.application.values import CategoryId, IdempotencyKey, Money

from . import pace_math
from .memory_store import MemoryStore


class MemoryBudgetGateway:
    """`/v1/budgets`의 대역. 대역은 예산을 달마다 따로 두지 않고 카테고리당 하나만 둔다."""

    def __init__(self, store: MemoryStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    async def statuses(self, period: Period) -> tuple[BudgetStatus, ...]:
        return tuple(
            self._status(c, period)
            for c in self._store.categories.values()
            if c.direction == Direction.EXPENSE
        )

    async def status(self, category_id: CategoryId, period: Period) -> BudgetStatus:
        return self._status(self._expense_category(category_id), period)

    async def set_limit(
        self, category_id: CategoryId, amount: Money | None, idempotency_key: IdempotencyKey
    ) -> BudgetStatus:
        category = self._expense_category(category_id)
        if amount is None:
            self._store.limits.pop(category_id, None)
        elif amount <= Money(0):
            raise LedgerValidationError({"amount": "예산은 0보다 커야 합니다."})
        else:
            self._store.limits[category_id] = amount
        # 예산 설정은 같은 값을 두 번 넣어도 결과가 같다. 키는 기록만 한다.
        self._store.replies[idempotency_key] = category_id
        return self._status(category, Period.of(self._clock.now().date()))

    def _expense_category(self, category_id: CategoryId) -> Category:
        category = self._store.categories.get(category_id)
        if category is None or category.direction != Direction.EXPENSE:
            raise LedgerValidationError({"category_id": "지출 카테고리가 아닙니다."})
        return category

    def _status(self, category: Category, period: Period) -> BudgetStatus:
        rows = self._store.matching(TransactionFilter(period, Direction.EXPENSE, category.id))
        spent = Money.total(t.amount for t in rows)
        limit = self._store.limits.get(category.id)
        if limit is None:
            return BudgetStatus(category, None, spent, None, None, None, None)
        through = pace_math.elapsed_days(period, self._clock.now().date())
        series = pace_math.cumulative(
            ((self._store.local_day(t).day, t.amount) for t in rows), through
        )
        return BudgetStatus(
            category=category,
            limit=limit,
            spent=spent,
            remaining=limit - spent,
            percent=spent.amount * 100 // limit.amount,
            projected=pace_math.project(spent, through, period.days),
            over_on=pace_math.day_in(period, pace_math.crossing_day(series, limit, period.days)),
        )
