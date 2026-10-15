from __future__ import annotations

from typing import Any

from pydantic import AwareDatetime, BaseModel

from ui.application.dto import RunCall, RunDetail

from .run_line_reply import RunLineReply


class _CallReply(BaseModel):
    call_id: str
    tool: str
    args: dict[str, Any]  # 자리마다 모양이 다른 저장된 JSON — 바깥과 닿는 자리라 Any다
    result: dict[str, Any] | None
    confirmed_at: AwareDatetime | None


class RunDetailReply(RunLineReply):
    """api `GET /v1/runs/{id}`의 응답 — 실행과 도구 호출들."""

    tool_calls: list[_CallReply]

    def detail(self) -> RunDetail:
        calls = tuple(
            RunCall(c.call_id, c.tool, c.args, c.result, c.confirmed_at) for c in self.tool_calls
        )
        return RunDetail(self.line(len(calls)), calls)
