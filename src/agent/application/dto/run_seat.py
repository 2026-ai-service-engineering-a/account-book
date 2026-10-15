from __future__ import annotations

from enum import StrEnum


class RunSeat(StrEnum):
    """실행이 시작된 자리 — agent가 여는 엔드포인트 하나. api의 CHECK와 같은 목록이다."""

    CAPTURE = "capture"
    CLASSIFY = "classify"
    CHAT = "chat"
    ASK = "ask"

    @property
    def flow(self) -> str:
        """자리마다 흐름이 정해져 있다(ai/agent-loop.md 3장). 채팅만 ReAct, 나머지는 단발."""
        return "react" if self is RunSeat.CHAT else "single"
