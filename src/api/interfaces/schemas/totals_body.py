from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import Totals


class TotalsBody(BaseModel):
    """지출 합과 수입 합(정수 원). 순액은 내지 않는다."""

    expense: int
    income: int

    @classmethod
    def of(cls, totals: Totals) -> TotalsBody:
        return cls(expense=totals.expense.amount, income=totals.income.amount)
