from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import AwareDatetime, BaseModel, PositiveInt

from agent.domain.tools import TransactionLine, TransactionList
from agent.domain.values import Amount, CategoryId, Direction


class _TransactionItem(TypedDict):
    id: str
    direction: Literal["expense", "income"]
    amount: PositiveInt
    occurred_at: AwareDatetime
    category_id: str
    merchant: str
    memo: str


class TransactionPageReply(BaseModel):
    """api `GET /v1/transactions`의 응답 본문. 도구가 쓰는 칸만 읽는다."""

    items: list[_TransactionItem]
    next_cursor: str | None

    def page(self) -> TransactionList:
        return TransactionList(
            transactions=tuple(
                TransactionLine(
                    id=i["id"],
                    occurred_at=i["occurred_at"],
                    direction=Direction(i["direction"]),
                    amount=Amount(i["amount"]),
                    category_id=CategoryId(i["category_id"]),
                    merchant=i["merchant"],
                    memo=i["memo"],
                )
                for i in self.items
            ),
            has_more=self.next_cursor is not None,
        )
