from __future__ import annotations

from enum import StrEnum


class AnswerStatus(StrEnum):
    """문서 Q&A 한 번의 끝 — 답했다 · 근거가 없다 · 찾은 조문만."""

    ANSWERED = "answered"
    ABSTAINED = "abstained"
    SEARCH_ONLY = "search_only"
