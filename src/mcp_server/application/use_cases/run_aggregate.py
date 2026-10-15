from __future__ import annotations

from datetime import date, datetime, time, timedelta, tzinfo

from mcp_server.application.dto import LedgerFilter
from mcp_server.application.ports import LedgerApi
from mcp_server.domain.tools import ToolName, ToolRequest
from mcp_server.domain.values import TimeRange

from .tool_payload import fit

_MAX_CHANGES = 30  # compare_periods의 카테고리 상한(docs/ai/tools.md 4.1)

type Outcome = tuple[dict[str, object], dict[str, object]]  # data, meta


class RunAggregate:
    """집계 하나 — 기간을 경계로 풀고, api를 한 번 부르고, 결과와 meta를 낸다.

    agent의 도구 실행기와 같은 모양을 낸다(docs/ai/tools.md 3장). 재시도하지 않는다.
    """

    def __init__(self, ledger: LedgerApi) -> None:
        self._ledger = ledger

    async def __call__(self, request: ToolRequest, today: date, zone: tzinfo) -> Outcome:
        """`today`는 사용자 타임존의 오늘이다. 기간 이름은 이것으로 푼다."""
        if request.name is ToolName.COMPARE_PERIODS:
            return await self._compare(request, today, zone)
        period = request.periods["period"].bounds(today, zone)
        periods = {"period": period}
        if request.name is ToolName.GET_BUDGET_STATUS:
            month = period.start.date()  # 예산은 달 단위다 — 기간이 시작하는 달
            lines = await self._ledger.budget_status(month, request.category_id)
            return _rows({"budgets": list(lines)}, "budgets", periods)
        where = LedgerFilter(period, request.category_id, request.merchant, request.direction)
        if request.name is ToolName.COUNT_FREQUENCY:
            return await self._ledger.frequency(where), _meta(1, False, periods)
        return await self._ledger.summary(where), _meta(1, False, periods)

    async def _compare(self, request: ToolRequest, today: date, zone: tzinfo) -> Outcome:
        a = request.periods["a"].bounds(today, zone)
        b = request.periods["b"].bounds(today, zone)
        a, aligned = _same_length(a, b, today, zone)
        shifts = await self._ledger.compare(a, b, request.category_id)
        data: dict[str, object] = {"changes": list(shifts[:_MAX_CHANGES])}
        data, meta = _rows(data, "changes", {"a": a, "b": b}, more=len(shifts) > _MAX_CHANGES)
        note = " ".join(filter(None, (aligned, str(meta.get("note", "")))))
        if note:
            meta["note"] = note
        return data, meta


def _rows(
    data: dict[str, object], key: str, periods: dict[str, TimeRange], more: bool = False
) -> Outcome:
    trimmed = fit(data, key)
    rows = data[key]
    count = len(rows) if isinstance(rows, list) else 0
    truncated = more or trimmed
    meta = _meta(count, truncated, periods)
    if truncated:
        meta["note"] = f"{count}줄까지만 보여줬다. 더 있다 — 기간이나 조건을 좁혀라."
    return data, meta


def _meta(count: int, truncated: bool, periods: dict[str, TimeRange]) -> dict[str, object]:
    return {
        "row_count": count,
        "truncated": truncated,
        "periods": {
            k: {"from": r.start.isoformat(), "to": r.end.isoformat()} for k, r in periods.items()
        },
    }


def _same_length(a: TimeRange, b: TimeRange, today: date, zone: tzinfo) -> tuple[TimeRange, str]:
    """b가 진행 중(오늘을 품었다)이면 a를 b가 지나온 날 수만큼 자른다.

    10월 8일에 "지난달보다 늘었어?"를 9월 전체와 견주면 늘 줄었다고 나온다.
    b가 오늘로 끝나면 다 지나온 것으로 본다 — 자르지 않는다. agent와 같은 규칙이다.
    """
    midnight = datetime.combine(today, time(0), tzinfo=zone)
    tomorrow = midnight + timedelta(days=1)
    if not b.start <= midnight < b.end or tomorrow >= b.end:
        return a, ""
    elapsed = tomorrow - b.start
    clipped = a.first(elapsed)
    if clipped == a:
        return a, ""
    return clipped, f"b가 진행 중이라 a를 같은 길이({elapsed.days}일)로 잘라 견줬다."
