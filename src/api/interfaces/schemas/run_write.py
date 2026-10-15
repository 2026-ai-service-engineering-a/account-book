from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field, model_validator

from api.application.dto import RunRecord
from api.domain.values import RunFlow, RunSeat, RunStatus

from .tool_call_write import ToolCallWrite

# 대화 한 번의 스텝 상한(8)에 스텝마다 부르는 도구 몇 개를 곱한 것보다 넉넉히. 끝은 둔다
MAX_TOOL_CALLS = 100


class RunWrite(BaseModel):
    """`POST /v1/runs`의 본문 — 끝난 실행 하나와 그 도구 호출들(api-contract 6장)."""

    id: str = Field(min_length=1, max_length=36)
    seat: RunSeat
    flow: RunFlow
    utterance: str
    model: str = Field(min_length=1, max_length=100)
    steps: int = Field(ge=0)
    tokens: int = Field(ge=0)
    cost_usd: Decimal = Field(ge=0, max_digits=10, decimal_places=6)
    status: RunStatus
    stop_reason: str = Field(min_length=1, max_length=30)
    tool_calls: list[ToolCallWrite] = Field(default_factory=list, max_length=MAX_TOOL_CALLS)
    client: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def _not_closed_by_writing(self) -> Self:
        # aborted는 대기인 제안을 닫을 때만 생긴다(/close) — 처음부터 aborted로 넣지 않는다
        if self.status is RunStatus.ABORTED:
            raise ValueError("aborted는 /v1/runs/{id}/close로만 된다")
        return self

    @model_validator(mode="after")
    def _unique_call_ids(self) -> Self:
        ids = [c.call_id for c in self.tool_calls]
        if len(ids) != len(set(ids)):
            raise ValueError("call_id는 실행 안에서 유일해야 합니다.")
        return self

    def record(self) -> RunRecord:
        return RunRecord(
            id=self.id,
            seat=self.seat,
            flow=self.flow,
            utterance=self.utterance,
            model=self.model,
            steps=self.steps,
            tokens=self.tokens,
            cost_usd=self.cost_usd,
            status=self.status,
            stop_reason=self.stop_reason,
            tool_calls=tuple(c.record() for c in self.tool_calls),
            client=self.client,
        )
