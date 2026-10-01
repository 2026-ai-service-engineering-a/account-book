from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import MonthTotal


class MonthTotalBody(BaseModel):
    period: str
    expense: int
    income: int

    @classmethod
    def of(cls, month: MonthTotal) -> MonthTotalBody:
        return cls(
            period=str(month.period), expense=month.expense.amount, income=month.income.amount
        )
