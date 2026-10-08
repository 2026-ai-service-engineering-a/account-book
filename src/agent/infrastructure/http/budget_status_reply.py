from __future__ import annotations

from datetime import date
from typing import TypedDict

from pydantic import RootModel

from agent.domain.tools import BudgetLine
from agent.domain.values import Amount, CategoryId


class _Category(TypedDict):
    id: str
    name: str


class _Status(TypedDict):
    category: _Category
    limit: int | None
    spent: int
    remaining: int | None
    percent: int | None
    projected: int | None
    over_on: date | None


class BudgetStatusReply(RootModel[list[_Status]]):
    """api `GET /v1/budgets/status`의 응답 본문 — 지출 카테고리 전부."""

    def lines(self) -> tuple[BudgetLine, ...]:
        return tuple(
            BudgetLine(
                category_id=CategoryId(s["category"]["id"]),
                name=s["category"]["name"],
                spent=Amount(s["spent"]),
                limit=_amount(s["limit"]),
                remaining=_amount(s["remaining"]),
                percent=s["percent"],
                projected=_amount(s["projected"]),
                over_on=s["over_on"],
            )
            for s in self.root
        )


def _amount(value: int | None) -> Amount | None:
    return Amount(value) if value is not None else None
