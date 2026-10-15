from __future__ import annotations

from enum import StrEnum


class RunSeat(StrEnum):
    """실행이 시작된 자리 — agent가 여는 엔드포인트 하나. api의 CHECK와 같은 목록이다."""

    CAPTURE = "capture"
    CLASSIFY = "classify"
    CHAT = "chat"
    ASK = "ask"
    INSIGHT = "insight"  # 리포트의 "눈에 띈 것"

    @property
    def flow(self) -> str:
        """자리마다 흐름이 정해져 있다(ai/agent-loop.md 3장)."""
        if self is RunSeat.CHAT:
            return "react"
        return "plan_execute" if self is RunSeat.INSIGHT else "single"
