from __future__ import annotations

from datetime import date
from typing import TypedDict

from pydantic import RootModel

from .amounts import amount


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
    """api `GET /v1/budgets/status`의 응답 본문 — 지출 카테고리 전부.
    예산을 정하지 않은 카테고리는 limit부터 아래가 None이다."""

    def rows(self) -> list[dict[str, object]]:
        return [
            {
                "category_id": s["category"]["id"],
                "name": s["category"]["name"],
                "spent": amount(s["spent"]),
                "limit": amount(s["limit"]),
                "remaining": amount(s["remaining"]),
                "percent": s["percent"],
                "projected": amount(s["projected"]),
                "over_on": s["over_on"].isoformat() if s["over_on"] else None,
            }
            for s in self.root
        ]
