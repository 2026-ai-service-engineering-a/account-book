from __future__ import annotations

from pydantic import BaseModel

from agent.domain.tools import SpendingTotals
from agent.domain.values import Amount


class TotalsReply(BaseModel):
    """api `GET /v1/summary`의 응답 본문."""

    expense: int
    income: int

    def totals(self) -> SpendingTotals:
        return SpendingTotals(Amount(self.expense), Amount(self.income))
