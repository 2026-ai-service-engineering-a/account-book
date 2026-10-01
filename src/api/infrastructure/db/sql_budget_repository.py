from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.orm import Session

from api.domain.values import CategoryId, Money, Period

from .rows import BudgetRow


class SqlBudgetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def limits(self, period: Period) -> dict[CategoryId, Money]:
        # 카테고리마다 그 달까지 가장 늦게 정한 행 하나. "YYYY-MM"은 글자순이 곧 시간순이다
        latest = (
            select(BudgetRow.category_id, BudgetRow.limit_amount)
            .where(BudgetRow.period <= str(period))
            .order_by(BudgetRow.category_id, BudgetRow.period.desc())
            .ext(distinct_on(BudgetRow.category_id))
        )
        return {
            CategoryId(category): Money(amount)
            for category, amount in self._session.execute(latest)
            if amount is not None  # 비어 있으면 그 달부터 예산 없음
        }

    def set_limit(self, category_id: CategoryId, period: Period, amount: Money | None) -> None:
        value = amount.amount if amount is not None else None
        statement = insert(BudgetRow).values(
            category_id=category_id, period=str(period), limit_amount=value
        )
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[BudgetRow.category_id, BudgetRow.period],
                set_={"limit_amount": statement.excluded.limit_amount},
            )
        )
