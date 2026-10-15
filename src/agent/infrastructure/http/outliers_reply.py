from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from pydantic import AwareDatetime, BaseModel

from agent.domain.tools import OutlierLine, OutlierReport, SkippedLine
from agent.domain.values import Amount, CategoryId, TimeRange


class _Transaction(TypedDict):
    id: str
    occurred_at: datetime
    category_id: str
    merchant: str
    amount: int


class _Item(TypedDict):
    transaction: _Transaction
    usual_median: int
    usual_upper: int


class _Skipped(TypedDict):
    category_id: str
    reason: str


class OutliersReply(BaseModel):
    """api `GET /v1/stats/outliers`의 응답 본문. 거래에서는 판정에 쓰는 칸만 읽는다."""

    baseline_from: AwareDatetime
    baseline_to: AwareDatetime
    items: list[_Item]
    truncated: bool
    skipped: list[_Skipped]

    def report(self) -> OutlierReport:
        return OutlierReport(
            baseline=TimeRange(self.baseline_from, self.baseline_to),
            items=tuple(
                OutlierLine(
                    id=i["transaction"]["id"],
                    occurred_at=i["transaction"]["occurred_at"],
                    category_id=CategoryId(i["transaction"]["category_id"]),
                    merchant=i["transaction"]["merchant"],
                    amount=Amount(i["transaction"]["amount"]),
                    usual_median=Amount(i["usual_median"]),
                    usual_upper=Amount(i["usual_upper"]),
                )
                for i in self.items
            ),
            truncated=self.truncated,
            skipped=tuple(
                SkippedLine(CategoryId(s["category_id"]), s["reason"]) for s in self.skipped
            ),
        )
