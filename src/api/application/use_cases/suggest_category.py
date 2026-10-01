from __future__ import annotations

from collections.abc import Callable

from api.application.dto import (
    CategoryCandidate,
    CategoryEvidence,
    CategoryQuery,
    CategorySearch,
    SearchStrategy,
)
from api.application.ports import UnitOfWork
from api.domain.rules.neighbor_vote import vote
from api.domain.rules.searchable_text import searchable_text, text_hash
from api.domain.values import CategoryId

# 1단계 — 같은 가맹점의 최근 5건 중 4건이 같은 카테고리면 끝난다
_HISTORY_WINDOW = 5
_HISTORY_AGREE = 4

# 단계 하나가 낸 것 — (길, 후보, 근거, 질의 벡터가 있으면 더 찾을 수 있나)
type _Found = tuple[
    SearchStrategy, tuple[CategoryCandidate, ...], tuple[CategoryEvidence, ...], bool
]
_NOTHING: _Found = (SearchStrategy.NONE, (), (), False)


class SuggestCategory:
    """`suggest_category` 도구의 자리 — 규칙 → 이력 → 벡터 이웃, 싼 것부터.

    여기서는 판단하지 않는다. 후보와 근거를 계산해 내려줄 뿐이고, LLM을 부를지는 agent가
    정한다(docs/ai/category-suggestion-rag.md 2장).
    """

    def __init__(
        self, unit_of_work: Callable[[], UnitOfWork], top_k: int, temperature: float
    ) -> None:
        self._unit_of_work = unit_of_work
        self._top_k = top_k
        self._temperature = temperature

    def __call__(self, query: CategoryQuery) -> CategorySearch:
        text = searchable_text(query.merchant, query.memo)
        with self._unit_of_work() as uow:
            categories = uow.catalog.categories(query.direction)
            allowed = {c.id for c in categories}
            found = (
                self._by_rule(uow, text, allowed)
                or self._by_history(uow, text, query, allowed)
                or self._by_vector(uow, text, query, allowed)
            )
        strategy, candidates, evidence, needs_vector = found
        return CategorySearch(strategy, text, needs_vector, candidates, evidence, categories)

    @staticmethod
    def _by_rule(uow: UnitOfWork, text: str, allowed: set[CategoryId]) -> _Found | None:
        matched = uow.index.rule_match(text, allowed) if text else None
        if matched is None:
            return None
        return SearchStrategy.RULE, (CategoryCandidate(matched, 1.0),), (), False

    @staticmethod
    def _by_history(
        uow: UnitOfWork, text: str, query: CategoryQuery, allowed: set[CategoryId]
    ) -> _Found | None:
        if not text:
            return None
        recent = [
            e
            for e in uow.index.recent_with_text(text_hash(text), query.direction, _HISTORY_WINDOW)
            if e.category_id in allowed
        ]
        counts: dict[CategoryId, int] = {}
        for e in recent:
            counts[e.category_id] = counts.get(e.category_id, 0) + 1
        winner = max(counts, key=lambda c: counts[c], default=None)
        if winner is None or counts[winner] < _HISTORY_AGREE:
            return None
        candidate = CategoryCandidate(winner, counts[winner] / len(recent))
        return SearchStrategy.HISTORY, (candidate,), tuple(recent), False

    def _by_vector(
        self, uow: UnitOfWork, text: str, query: CategoryQuery, allowed: set[CategoryId]
    ) -> _Found:
        model = query.embedding_model
        if not text or not model:
            return _NOTHING
        vector = uow.index.stored_vector(model, text_hash(text)) or query.query_vector
        if vector is None:
            return SearchStrategy.NONE, (), (), True
        neighbors = uow.index.nearest(model, vector, query.direction, allowed, self._top_k)
        if not neighbors:
            return _NOTHING
        ranked = vote([(e.similarity or 0.0, e.category_id) for e in neighbors], self._temperature)
        candidates = tuple(CategoryCandidate(c, min(1.0, p)) for c, p in ranked)
        return SearchStrategy.VECTOR, candidates, neighbors, False
