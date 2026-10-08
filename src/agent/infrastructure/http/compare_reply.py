from __future__ import annotations

from typing import TypedDict

from pydantic import RootModel

from agent.domain.tools import CategoryShift
from agent.domain.values import Amount, CategoryId


class _Category(TypedDict):
    id: str
    name: str


class _Change(TypedDict):
    category: _Category
    a: int
    b: int
    delta: int
    percent: int | None


class CompareReply(RootModel[list[_Change]]):
    """api `GET /v1/stats/compare`의 응답 본문 — 카테고리별 줄의 목록."""

    def shifts(self) -> tuple[CategoryShift, ...]:
        return tuple(
            CategoryShift(
                category_id=CategoryId(c["category"]["id"]),
                name=c["category"]["name"],
                a=Amount(c["a"]),
                b=Amount(c["b"]),
                delta=Amount(c["delta"]),
                percent=c["percent"],
            )
            for c in self.root
        )
