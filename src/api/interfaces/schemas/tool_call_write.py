from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from api.application.dto import ToolCallRecord


class ToolCallWrite(BaseModel):
    """`POST /v1/runs`에 실린 도구 호출 하나. 인자와 결과는 도구마다 모양이 달라 객체인지만 본다."""

    # 제공자가 정한다. Gemini의 id는 생각 서명이 붙어 150자를 넘는다. 끝은 두되 넉넉히
    call_id: str = Field(min_length=1, max_length=1000)
    tool: str = Field(min_length=1, max_length=50)
    # 바깥과 닿는 자리라 Any다(development-rules 5.2). 안으로는 Mapping으로 들어간다
    args: dict[str, Any]
    result: dict[str, Any] | None = None

    def record(self) -> ToolCallRecord:
        return ToolCallRecord(self.call_id, self.tool, self.args, self.result)
