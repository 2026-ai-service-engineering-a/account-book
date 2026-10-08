from __future__ import annotations

from dataclasses import dataclass

from .answer_status import AnswerStatus
from .document_hit import DocumentHit


@dataclass(frozen=True, slots=True)
class DocumentAnswer:
    """문서 Q&A의 답. 어떤 끝이든 찾은 조문(`chunks`)을 들고 온다 — 화면이 원문을 펼쳐 보인다."""

    status: AnswerStatus
    answer: str  # 답했을 때만
    citations: tuple[DocumentHit, ...]  # 답의 근거
    chunks: tuple[DocumentHit, ...]  # 찾은 조문 전부
    reason: str = ""  # 답하지 못한 까닭 한 줄
