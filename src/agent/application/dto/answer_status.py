from __future__ import annotations

from enum import StrEnum


class AnswerStatus(StrEnum):
    """문서 Q&A 한 번의 끝(docs/ai/document-rag.md 5.3·5.4)."""

    ANSWERED = "answered"  # 인용과 숫자 검증을 통과한 답
    ABSTAINED = "abstained"  # 조각에 근거가 없다 — 모른다고 답한다
    SEARCH_ONLY = "search_only"  # 생성이나 검증이 실패했다 — 찾은 조각만 보인다
