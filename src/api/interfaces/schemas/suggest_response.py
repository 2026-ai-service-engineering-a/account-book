from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.application.dto import CategorySearch

from .candidate_body import CandidateBody
from .category_body import CategoryBody
from .evidence_body import EvidenceBody


class SuggestResponse(BaseModel):
    """docs/ai/category-suggestion-rag.md 5장의 모양. 그 방향의 카테고리 사전을 같이 낸다."""

    strategy: Literal["rule", "history", "vector", "none"]
    query_text: str
    needs_query_vector: bool
    candidates: list[CandidateBody]
    evidence: list[EvidenceBody]
    categories: list[CategoryBody]

    @classmethod
    def of(cls, search: CategorySearch) -> SuggestResponse:
        return cls(
            strategy=search.strategy.value,
            query_text=search.query_text,
            needs_query_vector=search.needs_query_vector,
            candidates=[
                CandidateBody(category_id=c.category_id, confidence=c.confidence)
                for c in search.candidates
            ],
            evidence=[EvidenceBody.of(e) for e in search.evidence],
            categories=[CategoryBody.of(c) for c in search.categories],
        )
