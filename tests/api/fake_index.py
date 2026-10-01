"""카테고리 고르기의 검색 재료를 메모리에 — 색인 텍스트·벡터·규칙. 이웃은 코사인으로 실제로 잰다."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from api.application.dto import CategoryEvidence, IndexText
from api.domain.entities import Transaction
from api.domain.rules.searchable_text import searchable_text
from api.domain.rules.searchable_text import text_hash as text_hash_of
from api.domain.values import CategoryId, Direction

if TYPE_CHECKING:
    from .fakes import FakeTransactions


class FakeIndex:
    """색인 텍스트·벡터·규칙을 메모리에. 이웃은 코사인으로 실제로 잰다."""

    def __init__(self, transactions: FakeTransactions) -> None:
        self._transactions = transactions
        self.vectors: dict[tuple[str, str], tuple[float, ...]] = {}
        self.rules: dict[str, CategoryId] = {}

    def _text_of(self, t: Transaction) -> str:
        return searchable_text(t.merchant, t.memo)

    def rule_match(self, text: str, allowed: set[CategoryId]) -> CategoryId | None:
        return next((c for p, c in self.rules.items() if p in text and c in allowed), None)

    def recent_with_text(
        self, text_hash: str, direction: Direction, limit: int
    ) -> tuple[CategoryEvidence, ...]:
        rows = [
            t
            for t in self._transactions.rows.values()
            if text_hash_of(self._text_of(t)) == text_hash and t.direction is direction
        ]
        rows.sort(key=lambda t: t.occurred_at, reverse=True)
        return tuple(_evidence(t) for t in rows[:limit])

    def stored_vector(self, model: str, text_hash: str) -> tuple[float, ...] | None:
        return self.vectors.get((model, text_hash))

    def nearest(
        self,
        model: str,
        vector: tuple[float, ...],
        direction: Direction,
        allowed: set[CategoryId],
        limit: int,
    ) -> tuple[CategoryEvidence, ...]:
        latest: dict[tuple[str, str], Transaction] = {}
        for t in self._transactions.rows.values():
            key = (text_hash_of(self._text_of(t)), t.category_id)
            fits = t.direction is direction and t.category_id in allowed
            if fits and (key not in latest or t.occurred_at > latest[key].occurred_at):
                latest[key] = t
        scored = [
            (_cosine(vector, self.vectors[(model, h)]), t)
            for (h, _), t in latest.items()
            if (model, h) in self.vectors
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return tuple(_evidence(t, s) for s, t in scored[:limit])

    def pending(self, model: str, limit: int) -> tuple[IndexText, ...]:
        seen: dict[str, IndexText] = {}
        for t in self._transactions.rows.values():
            text = self._text_of(t)
            h = text_hash_of(text)
            if text and h not in seen and (model, h) not in self.vectors:
                seen[h] = IndexText(h, text)
        return tuple(seen.values())[:limit]

    def put_embedding(self, model: str, text_hash: str, vector: tuple[float, ...]) -> None:
        self.vectors[(model, text_hash)] = vector


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    norm = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def _evidence(t: Transaction, similarity: float | None = None) -> CategoryEvidence:
    return CategoryEvidence(
        t.id, t.merchant, t.memo, t.category_id, t.amount, t.occurred_at, similarity
    )
