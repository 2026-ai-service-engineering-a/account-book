from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentAnswerDraft:
    """LLM이 낸 답 그대로 — 아직 검증하지 않았다(docs/ai/document-rag.md 5.3)."""

    answer: str
    citations: tuple[str, ...]  # 프롬프트에 넘긴 조각의 짧은 id(c1, c2 …)
    abstain: bool
