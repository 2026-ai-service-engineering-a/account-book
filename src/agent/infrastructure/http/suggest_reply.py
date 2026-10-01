from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import AwareDatetime, BaseModel, PositiveInt

from agent.application.dto import (
    Candidate,
    CategoryEntry,
    Evidence,
    SearchResult,
    SearchStrategy,
)
from agent.domain.values import CategoryId, Confidence, Money


class _CandidateBody(TypedDict):
    category_id: str
    confidence: float


class _EvidenceBody(TypedDict):
    transaction_id: str
    merchant: str
    memo: str
    category_id: str
    amount: PositiveInt
    occurred_at: AwareDatetime
    similarity: float | None


class _CategoryBody(TypedDict):
    id: str
    name: str


class SuggestReply(BaseModel):
    """api `POST /v1/categories/suggest`의 응답 본문. 바깥에서 온 JSON이라 받자마자 검사한다.

    안쪽 모양(TypedDict)은 이 클래스만 쓴다(development-rules 1.2의 예외).
    """

    strategy: Literal["rule", "history", "vector", "none"]
    query_text: str
    needs_query_vector: bool
    candidates: list[_CandidateBody]
    evidence: list[_EvidenceBody]
    categories: list[_CategoryBody]

    def result(self) -> SearchResult:
        return SearchResult(
            strategy=SearchStrategy(self.strategy),
            query_text=self.query_text,
            needs_query_vector=self.needs_query_vector,
            candidates=tuple(
                Candidate(CategoryId(c["category_id"]), Confidence(c["confidence"]))
                for c in self.candidates
            ),
            evidence=tuple(
                Evidence(
                    transaction_id=e["transaction_id"],
                    merchant=e["merchant"],
                    memo=e["memo"],
                    category_id=CategoryId(e["category_id"]),
                    amount=Money(e["amount"]),
                    day=e["occurred_at"].date(),
                    similarity=e["similarity"],
                )
                for e in self.evidence
            ),
            categories=tuple(
                CategoryEntry(CategoryId(c["id"]), c["name"]) for c in self.categories
            ),
        )
