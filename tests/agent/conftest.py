from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from agent.application.dto import Prompt

SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 10, 1, 18, 0, tzinfo=SEOUL)
SENTENCE = "오늘 오후 3시에 카페에서 5천원 썼어"


def extraction(**overrides: object) -> dict[str, object]:
    """SENTENCE를 제대로 읽은 답. 바꿀 키만 넘긴다."""
    base: dict[str, object] = {
        "kind": "record",
        "amount": 5000,
        "direction": "expense",
        "payment": "unknown",
        "merchant": "카페",
        "day": "today",
        "month": 0,
        "day_of_month": 0,
        "hour": 15,
        "minute": 0,
    }
    return base | overrides


class FakeModel:
    """고정 응답을 차례로 내는 LLM. 테스트는 실제 모델을 부르지 않는다(development-rules 4.3)."""

    def __init__(self, *replies: Mapping[str, object] | Exception) -> None:
        self._replies = list(replies)
        self.prompts: list[Prompt] = []

    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        self.prompts.append(prompt)
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply
