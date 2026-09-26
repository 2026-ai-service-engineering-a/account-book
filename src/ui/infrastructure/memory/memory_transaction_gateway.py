from __future__ import annotations

from ui.application.dto import (
    Source,
    Transaction,
    TransactionDraft,
    TransactionFilter,
    TransactionPage,
)
from ui.application.errors import LedgerValidationError, TransactionNotFound
from ui.application.values import TransactionId

from .memory_store import MemoryStore


class MemoryTransactionGateway:
    """`/v1/transactions`의 대역. 멱등성 키도 흉내 낸다 — 두 번 눌러도 한 건이다."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def exists_any(self) -> bool:
        return bool(self._store.transactions)

    async def search(
        self, criteria: TransactionFilter, cursor: str | None = None, limit: int = 50
    ) -> TransactionPage:
        rows = sorted(
            self._store.matching(criteria), key=lambda t: (t.occurred_at, t.id), reverse=True
        )
        # 진짜 api의 커서는 불투명한 문자열이다. 대역은 오프셋을 문자열로 쓴다.
        start = int(cursor) if cursor and cursor.isdigit() else 0
        end = start + min(limit, 200)
        return TransactionPage(
            items=tuple(rows[start:end]), next_cursor=str(end) if end < len(rows) else None
        )

    async def get(self, transaction_id: TransactionId) -> Transaction:
        found = self._store.transactions.get(transaction_id)
        if found is None:
            raise TransactionNotFound(transaction_id)
        return found

    async def create(
        self, draft: TransactionDraft, idempotency_key: str, run_id: str | None = None
    ) -> Transaction:
        replayed = self._replay(idempotency_key)
        if replayed is not None:
            return replayed
        self._check(draft)
        created = self._build(
            self._store.next_id(), draft, Source.AGENT if run_id else Source.MANUAL
        )
        self._store.transactions[created.id] = created
        self._store.replies[idempotency_key] = created.id
        return created

    async def update(
        self, transaction_id: TransactionId, draft: TransactionDraft, idempotency_key: str
    ) -> Transaction:
        existing = await self.get(transaction_id)
        self._check(draft)
        updated = self._build(existing.id, draft, existing.source)
        self._store.transactions[existing.id] = updated
        self._store.replies[idempotency_key] = existing.id
        return updated

    async def delete(self, transaction_id: TransactionId, idempotency_key: str) -> None:
        if idempotency_key in self._store.replies:
            return
        await self.get(transaction_id)
        del self._store.transactions[transaction_id]
        self._store.replies[idempotency_key] = transaction_id

    def _replay(self, idempotency_key: str) -> Transaction | None:
        previous = self._store.replies.get(idempotency_key)
        return self._store.transactions.get(TransactionId(previous)) if previous else None

    def _check(self, draft: TransactionDraft) -> None:
        errors = self._store.validate(draft)
        if errors:
            raise LedgerValidationError(errors)

    @staticmethod
    def _build(
        transaction_id: TransactionId, draft: TransactionDraft, source: Source
    ) -> Transaction:
        return Transaction(
            id=transaction_id,
            direction=draft.direction,
            amount=draft.amount,
            occurred_at=draft.occurred_at,
            category_id=draft.category_id,
            account_id=draft.account_id,
            merchant=draft.merchant.strip(),
            memo=draft.memo.strip(),
            source=source,
        )
