from __future__ import annotations

from datetime import date
from typing import Protocol

from mcp_server.application.dto import LedgerFilter
from mcp_server.domain.values import TimeRange

type Row = dict[str, object]


class LedgerApi(Protocol):
    """api의 집계 넷. 답은 이미 도구 결과의 모양이다 — 금액은 `{amount, currency}`다
    (docs/ai/tools.md 3.2). 거절은 `LedgerRejected`, 닿지 못하면 `LedgerUnavailable`."""

    async def summary(self, where: LedgerFilter) -> Row: ...

    async def frequency(self, where: LedgerFilter) -> Row: ...

    async def compare(self, a: TimeRange, b: TimeRange, category_id: str) -> list[Row]: ...

    async def budget_status(self, month: date, category_id: str) -> list[Row]: ...
