from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .tool_call import ToolCall

type TurnRole = Literal["user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class Turn:
    """도구를 쓰는 대화의 한 칸.

    - user: 사용자 발화(`text`). 바깥 데이터라 마커로 감싼 채 들어온다.
    - assistant: 모델이 고른 도구 호출(`tool_calls`)이나 답(`text`).
    - tool: 도구 결과 봉투(`text`, JSON)와 그 호출의 `call_id`.
    """

    role: TurnRole
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    call_id: str = ""

    def __post_init__(self) -> None:
        if (self.role == "tool") != bool(self.call_id):
            raise ValueError("call_id는 tool 칸에만 있다")
        if self.tool_calls and self.role != "assistant":
            raise ValueError("도구 호출은 assistant 칸에만 있다")
