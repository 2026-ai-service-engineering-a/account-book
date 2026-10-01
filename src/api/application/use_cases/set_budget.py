from __future__ import annotations

from api.application.dto import BudgetStatus
from api.application.ports import Clock, UnitOfWork
from api.domain.errors import ConfirmationRequired, InvalidTransaction
from api.domain.values import CategoryId, Direction, Money, Period

from .read_budget_statuses import statuses


class SetBudget:
    """카테고리 예산을 이번 달부터 바꾼다 — `set_budget` 도구의 자리. 언제나 확인이 필요하다
    (README 4장). `None`이면 이번 달부터 예산 없음.

    커밋은 부르는 쪽(멱등 쓰기)이 한다. 바꾼 뒤의 이번 달 상태를 돌려준다.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def __call__(
        self, uow: UnitOfWork, category_id: CategoryId, amount: Money | None, *, confirmed: bool
    ) -> BudgetStatus:
        expense = {c.id for c in uow.catalog.categories(Direction.EXPENSE)}
        if category_id not in expense:
            raise InvalidTransaction({"category_id": "지출 카테고리가 아닙니다."})
        if amount is not None and amount.amount <= 0:
            raise InvalidTransaction({"amount": "예산은 0보다 커야 합니다."})
        if not confirmed:
            raise ConfirmationRequired
        period = Period.of(self._clock.now().date())
        uow.budgets.set_limit(category_id, period, amount)
        (status,) = statuses(uow, self._clock, period, category_id)
        return status
