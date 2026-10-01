from __future__ import annotations

from sqlalchemy import delete, select, tuple_
from sqlalchemy.orm import Session

from api.application.dto import TransactionPage, TransactionQuery
from api.domain.entities import Transaction
from api.domain.values import AccountId, CategoryId, Direction, Money, Source, TransactionId

from .page_cursor import decode_cursor, encode_cursor
from .rows import TransactionRow
from .transaction_filter import filter_conditions


class SqlTransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, transaction_id: TransactionId) -> Transaction | None:
        row = self._session.get(TransactionRow, transaction_id)
        return _entity(row) if row else None

    def search(self, query: TransactionQuery) -> TransactionPage:
        statement = select(TransactionRow).where(*filter_conditions(query))
        after = decode_cursor(query.cursor) if query.cursor else None
        if after is not None:
            statement = statement.where(
                tuple_(TransactionRow.occurred_at, TransactionRow.id) < tuple_(*after)
            )
        statement = statement.order_by(
            TransactionRow.occurred_at.desc(), TransactionRow.id.desc()
        ).limit(query.limit + 1)  # 하나 더 읽어 다음 쪽이 있는지 안다
        rows = self._session.scalars(statement).all()
        page, more = rows[: query.limit], len(rows) > query.limit
        last = page[-1] if page else None
        cursor = encode_cursor(last.occurred_at, last.id) if more and last else None
        return TransactionPage(tuple(_entity(r) for r in page), cursor)

    def add(self, transaction: Transaction) -> None:
        self._session.add(_row(transaction))
        self._session.flush()

    def replace(self, transaction: Transaction) -> None:
        self._session.merge(_row(transaction))
        self._session.flush()

    def remove(self, transaction_id: TransactionId) -> None:
        self._session.execute(delete(TransactionRow).where(TransactionRow.id == transaction_id))


def _entity(row: TransactionRow) -> Transaction:
    return Transaction(
        id=TransactionId(row.id),
        direction=Direction(row.direction),
        amount=Money(row.amount),
        occurred_at=row.occurred_at,
        category_id=CategoryId(row.category_id),
        account_id=AccountId(row.account_id),
        merchant=row.merchant,
        memo=row.memo,
        source=Source(row.source),
        run_id=row.run_id,
    )


def _row(transaction: Transaction) -> TransactionRow:
    return TransactionRow(
        id=transaction.id,
        direction=transaction.direction.value,
        amount=transaction.amount.amount,
        occurred_at=transaction.occurred_at,
        category_id=transaction.category_id,
        account_id=transaction.account_id,
        merchant=transaction.merchant,
        memo=transaction.memo,
        source=transaction.source.value,
        run_id=transaction.run_id,
    )
