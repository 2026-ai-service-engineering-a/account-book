from __future__ import annotations

from decimal import Decimal

from pydantic import AwareDatetime, BaseModel

from ui.application.dto import RunLine
from ui.application.values import RunId


class RunLineReply(BaseModel):
    """api가 낸 실행 한 줄. 바깥에서 온 JSON이라 받자마자 검사한다."""

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
    client: str | None = None
    created_at: AwareDatetime
    tool_count: int = 0

    def line(self, tool_count: int | None = None) -> RunLine:
        return RunLine(
            id=RunId(self.id),
            seat=self.seat,
            flow=self.flow,
            utterance=self.utterance,
            model=self.model,
            steps=self.steps,
            tokens=self.tokens,
            cost_usd=self.cost_usd,
            status=self.status,
            stop_reason=self.stop_reason,
            client=self.client,
            created_at=self.created_at,
            tool_count=self.tool_count if tool_count is None else tool_count,
        )
