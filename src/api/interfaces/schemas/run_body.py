from __future__ import annotations

from typing import Any

from pydantic import AwareDatetime, BaseModel

from api.application.dto import RunRecord


class _CallBody(BaseModel):
    call_id: str
    tool: str
    args: dict[str, Any]  # 바깥과 닿는 자리라 Any다(development-rules 5.2)
    result: dict[str, Any] | None
    confirmed_at: AwareDatetime | None


class RunBody(BaseModel):
    """감사 로그의 실행 한 줄 — 쓰기 제안을 되살릴 때 agent가 읽는다(api-contract 6장)."""

    id: str
    seat: str
    flow: str
    utterance: str
    status: str
    stop_reason: str
    client: str | None
    created_at: AwareDatetime | None
    tool_calls: list[_CallBody]

    @classmethod
    def of(cls, run: RunRecord) -> RunBody:
        return cls(
            id=run.id,
            seat=run.seat.value,
            flow=run.flow.value,
            utterance=run.utterance,
            status=run.status.value,
            stop_reason=run.stop_reason,
            client=run.client,
            created_at=run.created_at,
            tool_calls=[
                _CallBody(
                    call_id=c.call_id,
                    tool=c.tool,
                    args=dict(c.args),
                    result=dict(c.result) if c.result is not None else None,
                    confirmed_at=c.confirmed_at,
                )
                for c in run.tool_calls
            ],
        )
