from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from zoneinfo import ZoneInfo

from agent.application.dto import (
    Candidate,
    CategoryEntry,
    CategoryQuery,
    Evidence,
    PendingText,
    Prompt,
    SearchResult,
    SearchStrategy,
)
from agent.application.errors import ModelUnavailable
from agent.domain.values import CategoryId, Confidence, Money

SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 10, 1, 18, 0, tzinfo=SEOUL)
SENTENCE = "오늘 오후 3시에 카페에서 5천원 썼어"


def extraction(**overrides: object) -> dict[str, object]:
    """SENTENCE를 제대로 읽은 답. 바꿀 키만 넘긴다."""
    base: dict[str, object] = {
        "kind": "record",
        "amount": 5000,
        "direction": "expense",
        "payment": "unknown",
        "merchant": "카페",
        "day": "today",
        "month": 0,
        "day_of_month": 0,
        "hour": 15,
        "minute": 0,
    }
    return base | overrides


class FakeModel:
    """고정 응답을 차례로 내는 LLM. 테스트는 실제 모델을 부르지 않는다(development-rules 4.3)."""

    def __init__(self, *replies: Mapping[str, object] | Exception) -> None:
        self._replies = list(replies)
        self.prompts: list[Prompt] = []

    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        self.prompts.append(prompt)
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


EXPENSE_CATEGORIES = (
    CategoryEntry(CategoryId("food"), "식비"),
    CategoryEntry(CategoryId("cafe"), "카페"),
    CategoryEntry(CategoryId("living"), "생활"),
)


def evidence(tid: str, merchant: str, category: str, similarity: float | None = None) -> Evidence:
    return Evidence(
        tid, merchant, "", CategoryId(category), Money(5800), date(2026, 9, 12), similarity
    )


def search(
    strategy: str = "vector",
    candidates: Sequence[tuple[str, float]] = (("cafe", 0.9), ("food", 0.1)),
    found: Sequence[Evidence] = (),
    needs_query_vector: bool = False,
    query_text: str = "블루보틀",
) -> SearchResult:
    if not found and candidates:
        found = (evidence("t1", "스타벅스", "cafe", 0.71), evidence("t2", "김밥천국", "food", 0.6))
    return SearchResult(
        strategy=SearchStrategy(strategy),
        query_text=query_text,
        needs_query_vector=needs_query_vector,
        candidates=tuple(Candidate(CategoryId(c), Confidence(p)) for c, p in candidates),
        evidence=tuple(found),
        categories=EXPENSE_CATEGORIES,
    )


class FakeLedger:
    """api 자리. 검색 답을 차례로 내고, 색인 쓰기를 기억한다."""

    def __init__(
        self, *results: SearchResult | Exception, pending: Sequence[PendingText] = ()
    ) -> None:
        self._results = list(results)
        self.queries: list[CategoryQuery] = []
        self._pending = list(pending)
        self.puts: dict[str, tuple[float, ...]] = {}

    async def suggest(self, query: CategoryQuery) -> SearchResult:
        self.queries.append(query)
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    async def pending(self, embedding_model: str, limit: int) -> tuple[PendingText, ...]:
        return tuple(p for p in self._pending if p.text_hash not in self.puts)[:limit]

    async def put_embedding(
        self, text_hash: str, embedding_model: str, vector: tuple[float, ...]
    ) -> None:
        self.puts[text_hash] = vector


class FakeEmbedder:
    """글자 수를 벡터로 쓰는 가짜 임베더(category-suggestion-rag 9장). 제공자를 부르지 않는다."""

    model = "fake/embedding@2"

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.calls: list[list[str]] = []

    async def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        self.calls.append(list(texts))
        if self._fail:
            raise ModelUnavailable("fake")
        return tuple((float(len(t)), 1.0) for t in texts)
