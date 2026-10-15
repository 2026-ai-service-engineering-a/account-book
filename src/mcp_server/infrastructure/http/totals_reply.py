from __future__ import annotations

from pydantic import BaseModel

from .amounts import amount


class TotalsReply(BaseModel):
    """api `GET /v1/summary`의 응답 본문."""

    expense: int
    income: int

    def row(self) -> dict[str, object]:
        return {"expense": amount(self.expense), "income": amount(self.income)}
