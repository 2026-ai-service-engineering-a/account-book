from __future__ import annotations

from ui.application.dto import (
    CategoryCandidate,
    CategoryEvidence,
    CategoryQuery,
    CategorySearch,
    IndexText,
    SearchStrategy,
    Transaction,
)
from ui.application.values import CategoryId, TextHash

from .memory_store import MemoryStore
from .neighbor_vote import cosine, vote
from .searchable_text import searchable_text, text_hash

# 1단계 — 같은 가맹점의 최근 5건 중 4건이 같은 카테고리면 끝난다
_HISTORY_WINDOW = 5
_HISTORY_AGREE = 4

# 단계 하나가 낸 것 — (길, 후보, 근거, 질의 벡터가 있으면 더 찾을 수 있나)
type _Found = tuple[
    SearchStrategy, tuple[CategoryCandidate, ...], tuple[CategoryEvidence, ...], bool
]
_NOTHING: _Found = (SearchStrategy.NONE, (), (), False)


class MemoryCategoryIndex:
    """`/v1/categories/suggest`와 색인의 메모리 대역. 규칙 → 이력 → 벡터 이웃, 싼 것부터.

    여기서는 판단하지 않는다. 후보와 근거를 계산해 내려줄 뿐이고, LLM을 부를지는 agent가
    정한다(docs/ai/category-suggestion-rag.md 2장).
    """

    def __init__(self, store: MemoryStore, top_k: int, temperature: float) -> None:
        self._store = store
        self._top_k = top_k
        self._temperature = temperature

    async def suggest(self, query: CategoryQuery) -> CategorySearch:
        text = searchable_text(query.merchant, query.memo)
        categories = tuple(
            c for c in self._store.categories.values() if c.direction == query.direction
        )
        allowed = {c.id for c in categories}
        rows = [
            t
            for t in self._store.transactions.values()
            if t.direction == query.direction and t.category_id in allowed
        ]
        found = self._by_rule(text, allowed) or self._by_history(text, rows)
        if found is None:
            found = self._by_vector(text, rows, query)
        strategy, candidates, evidence, needs_vector = found
        return CategorySearch(strategy, text, needs_vector, candidates, evidence, categories)

    async def pending(self, embedding_model: str, limit: int) -> tuple[IndexText, ...]:
        seen: dict[TextHash, IndexText] = {}
        for t in self._store.transactions.values():
            text = searchable_text(t.merchant, t.memo)
            key = text_hash(text)
            if text and key not in seen and (embedding_model, key) not in self._store.embeddings:
                seen[key] = IndexText(key, text)
                if len(seen) == limit:
                    break
        return tuple(seen.values())

    async def put_embedding(
        self, text_hash: TextHash, embedding_model: str, vector: tuple[float, ...]
    ) -> None:
        self._store.embeddings[(embedding_model, text_hash)] = vector

    def _by_rule(self, text: str, allowed: set[CategoryId]) -> _Found | None:
        for pattern, category_id in self._store.rules.items():
            if text and pattern in text and category_id in allowed:
                return SearchStrategy.RULE, (CategoryCandidate(category_id, 1.0),), (), False
        return None

    def _by_history(self, text: str, rows: list[Transaction]) -> _Found | None:
        same = [t for t in rows if text and searchable_text(t.merchant, t.memo) == text]
        recent = sorted(same, key=lambda t: t.occurred_at, reverse=True)[:_HISTORY_WINDOW]
        counts: dict[CategoryId, int] = {}
        for t in recent:
            counts[t.category_id] = counts.get(t.category_id, 0) + 1
        winner = max(counts, key=lambda c: counts[c], default=None)
        if winner is None or counts[winner] < _HISTORY_AGREE:
            return None
        candidate = CategoryCandidate(winner, counts[winner] / len(recent))
        return SearchStrategy.HISTORY, (candidate,), tuple(_evidence(t) for t in recent), False

    def _by_vector(self, text: str, rows: list[Transaction], query: CategoryQuery) -> _Found:
        model = query.embedding_model
        if not text or not model:
            return _NOTHING
        vector = self._store.embeddings.get((model, text_hash(text))) or query.query_vector
        if vector is None:
            return SearchStrategy.NONE, (), (), True
        neighbors = sorted(
            (
                (cosine(vector, stored), t)
                for t in _latest_per_text(rows)
                if (stored := self._store.embeddings.get((model, _hash_of(t)))) is not None
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )[: self._top_k]
        if not neighbors:
            return _NOTHING
        ranked = vote([(s, t.category_id) for s, t in neighbors], self._temperature)
        candidates = tuple(CategoryCandidate(c, min(1.0, p)) for c, p in ranked)
        evidence = tuple(_evidence(t, s) for s, t in neighbors)
        return SearchStrategy.VECTOR, candidates, evidence, False


def _hash_of(transaction: Transaction) -> TextHash:
    return text_hash(searchable_text(transaction.merchant, transaction.memo))


def _latest_per_text(rows: list[Transaction]) -> list[Transaction]:
    """같은 텍스트·카테고리는 이웃 하나로 센다. 자주 간 곳 한 군데가 투표를 독차지하지 않게.

    대표는 가장 최근 거래다 — 근거 줄에 보이는 날짜가 최근이어야 사람이 믿는다.
    """
    latest: dict[tuple[TextHash, CategoryId], Transaction] = {}
    for t in rows:
        key = (_hash_of(t), t.category_id)
        if key not in latest or t.occurred_at > latest[key].occurred_at:
            latest[key] = t
    return list(latest.values())


def _evidence(t: Transaction, similarity: float | None = None) -> CategoryEvidence:
    return CategoryEvidence(
        t.id, t.merchant, t.memo, t.category_id, t.amount, t.occurred_at, similarity
    )
