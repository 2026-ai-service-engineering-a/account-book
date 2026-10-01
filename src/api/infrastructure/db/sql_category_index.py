from __future__ import annotations

from typing import cast

from sqlalchemy import and_, func, literal, select
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.orm import Session

from api.application.dto import CategoryEvidence, IndexText
from api.domain.values import CategoryId, Direction, Money, TransactionId

from .rows import CategoryRuleRow, TextEmbeddingRow, TransactionRow

# HNSW 인덱스로 가까운 텍스트를 넉넉히 뽑은 뒤 방향·카테고리로 거른다. 거르고 나서 k개가
# 남도록 몇 배를 뽑나 — 다른 방향의 텍스트나 질의 텍스트 자신이 끼어든다.
_WIDEN = 4


class SqlCategoryIndex:
    """카테고리 고르기의 검색 재료를 SQL로 — 이웃 찾기는 pgvector의 코사인 거리(`<=>`)다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def rule_match(self, text: str, allowed: set[CategoryId]) -> CategoryId | None:
        statement = (
            select(CategoryRuleRow.category_id)
            .where(
                literal(text).contains(CategoryRuleRow.merchant_pattern),
                CategoryRuleRow.category_id.in_(allowed),
            )
            .order_by(func.length(CategoryRuleRow.merchant_pattern).desc())  # 긴 패턴이 이긴다
            .limit(1)
        )
        found = self._session.scalar(statement)
        return CategoryId(found) if found else None

    def recent_with_text(
        self, text_hash: str, direction: Direction, limit: int
    ) -> tuple[CategoryEvidence, ...]:
        statement = (
            select(TransactionRow)
            .where(
                TransactionRow.text_hash == text_hash, TransactionRow.direction == direction.value
            )
            .order_by(TransactionRow.occurred_at.desc())
            .limit(limit)
        )
        return tuple(_evidence(row) for row in self._session.scalars(statement))

    def stored_vector(self, model: str, text_hash: str) -> tuple[float, ...] | None:
        row = self._session.get(TextEmbeddingRow, (model, text_hash))
        return tuple(float(x) for x in row.vector) if row is not None else None

    def nearest(
        self,
        model: str,
        vector: tuple[float, ...],
        direction: Direction,
        allowed: set[CategoryId],
        limit: int,
    ) -> tuple[CategoryEvidence, ...]:
        distance = TextEmbeddingRow.vector.cosine_distance(list(vector))
        near = (
            select(TextEmbeddingRow.text_hash, (1 - distance).label("similarity"))
            .where(TextEmbeddingRow.model == model)
            .order_by(distance)
            .limit(limit * _WIDEN)
            .subquery()
        )
        # 같은 텍스트·카테고리는 이웃 하나 — 대표는 가장 최근 거래다
        statement = (
            select(TransactionRow, near.c.similarity)
            .join(near, near.c.text_hash == TransactionRow.text_hash)
            .where(
                and_(
                    TransactionRow.direction == direction.value,
                    TransactionRow.category_id.in_(allowed),
                )
            )
            .order_by(
                TransactionRow.text_hash,
                TransactionRow.category_id,
                TransactionRow.occurred_at.desc(),
            )
            .ext(distinct_on(TransactionRow.text_hash, TransactionRow.category_id))
        )
        # pgvector의 거리 식은 타입이 없어 유사도 열이 object로 온다. 여기서 실수로 바꾼다
        rows: list[tuple[TransactionRow, float]] = [
            (cast(TransactionRow, row), float(cast(float, similarity)))
            for row, similarity in self._session.execute(statement)
        ]
        rows.sort(key=lambda pair: pair[1], reverse=True)
        return tuple(_evidence(row, similarity) for row, similarity in rows[:limit])

    def pending(self, model: str, limit: int) -> tuple[IndexText, ...]:
        embedded = select(TextEmbeddingRow.text_hash).where(TextEmbeddingRow.model == model)
        statement = (
            select(TransactionRow.text_hash, TransactionRow.search_text)
            .where(TransactionRow.text_hash != "", TransactionRow.text_hash.not_in(embedded))
            .distinct()
            .limit(limit)
        )
        return tuple(IndexText(h, t) for h, t in self._session.execute(statement))

    def put_embedding(self, model: str, text_hash: str, vector: tuple[float, ...]) -> None:
        statement = insert(TextEmbeddingRow).values(
            model=model, text_hash=text_hash, vector=list(vector)
        )
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[TextEmbeddingRow.model, TextEmbeddingRow.text_hash],
                set_={"vector": statement.excluded.vector, "updated_at": func.now()},
            )
        )


def _evidence(row: TransactionRow, similarity: float | None = None) -> CategoryEvidence:
    return CategoryEvidence(
        transaction_id=TransactionId(row.id),
        merchant=row.merchant,
        memo=row.memo,
        category_id=CategoryId(row.category_id),
        amount=Money(row.amount),
        occurred_at=row.occurred_at,
        similarity=similarity,
    )
