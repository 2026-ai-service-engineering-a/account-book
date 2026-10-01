from __future__ import annotations

from enum import StrEnum


class ExtractionKind(StrEnum):
    """LLM이 본 한 줄의 종류. 기록이 아니면 칸을 채우지 않는다."""

    RECORD = "record"
    QUESTION = "question"
    CANCELLATION = "cancellation"  # 승인 취소 문자
    UNREADABLE = "unreadable"
