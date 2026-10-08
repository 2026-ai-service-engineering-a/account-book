from __future__ import annotations

from dataclasses import dataclass

from .answer_status import AnswerStatus
from .retrieval import Retrieval
from .retrieved_chunk import RetrievedChunk


@dataclass(frozen=True, slots=True)
class DocumentAnswer:
    """문서 Q&A의 결과. 어떤 끝이든 찾은 조각은 들고 간다 — 화면이 원문을 보인다."""

    status: AnswerStatus
    answer: str  # 답했을 때만. 아니면 비어 있다
    citations: tuple[RetrievedChunk, ...]  # 답이 인용한 조각, 인용 순서대로
    retrieval: Retrieval
    reason: str = ""  # 답하지 못한 까닭 — 운영 로그와 화면의 한 줄

    @property
    def chunks(self) -> tuple[RetrievedChunk, ...]:
        return self.retrieval.chunks
