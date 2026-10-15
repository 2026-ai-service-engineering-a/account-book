from __future__ import annotations

from decimal import Decimal

from pydantic import AwareDatetime, BaseModel

from api.application.dto import RunPage, RunSummary


class _RunLine(BaseModel):
    id: str
    seat: str
    flow: str
    utterance: str
    model: str
    steps: int
    tokens: int
    cost_usd: Decimal
    status: str
    stop_reason: str
    client: str | None
    created_at: AwareDatetime | None
    tool_count: int

    @classmethod
    def of(cls, line: RunSummary) -> _RunLine:
        run = line.run
        return cls(
            id=run.id,
            seat=run.seat.value,
            flow=run.flow.value,
            utterance=run.utterance,
            model=run.model,
            steps=run.steps,
            tokens=run.tokens,
            cost_usd=run.cost_usd,
            status=run.status.value,
            stop_reason=run.stop_reason,
            client=run.client,
            created_at=run.created_at,
            tool_count=line.tool_count,
        )


class RunPageBody(BaseModel):
    """실행 목록 한 쪽 — 줄마다 도구 호출의 수만. `next_cursor`가 없으면 마지막 쪽이다."""

    items: list[_RunLine]
    next_cursor: str | None

    @classmethod
    def of(cls, page: RunPage) -> RunPageBody:
        return cls(items=[_RunLine.of(line) for line in page.items], next_cursor=page.next_cursor)
