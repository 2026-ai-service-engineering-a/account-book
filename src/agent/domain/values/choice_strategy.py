from __future__ import annotations

from enum import StrEnum


class ChoiceStrategy(StrEnum):
    """카테고리가 어느 길로 정해졌나. "왜 이렇게 붙었지"에 답하고, 평가에서 단계별로 잰다."""

    RULE = "rule"
    HISTORY = "history"
    VECTOR = "vector"
    LLM = "llm"
    NONE = "none"  # 고르지 않았다 — 사람이 고른다
