from __future__ import annotations

from enum import StrEnum


class RunSeat(StrEnum):
    """에이전트 실행이 어느 자리에서 시작됐나 — agent가 여는 엔드포인트 하나가 자리 하나다.

    자리가 늘면 값과 CHECK 제약을 같이 늘린다(development-rules 6.6).
    """

    CAPTURE = "capture"
    CLASSIFY = "classify"
    CHAT = "chat"
    ASK = "ask"
    INSIGHT = "insight"  # 리포트의 "눈에 띈 것"(docs/ai/agentic-reports.md)
