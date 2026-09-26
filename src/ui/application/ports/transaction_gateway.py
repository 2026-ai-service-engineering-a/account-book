from __future__ import annotations

from typing import Protocol

from ui.application.dto import Transaction, TransactionDraft, TransactionFilter, TransactionPage
from ui.application.values import TransactionId


class TransactionGateway(Protocol):
    """api의 `/v1/transactions`. 지금은 메모리 대역, 나중에 HTTP 클라이언트가 채운다."""

    async def exists_any(self) -> bool: ...

    async def search(
        self, criteria: TransactionFilter, cursor: str | None = None, limit: int = 50
    ) -> TransactionPage: ...

    async def get(self, transaction_id: TransactionId) -> Transaction: ...

    async def create(
        self, draft: TransactionDraft, idempotency_key: str, run_id: str | None = None
    ) -> Transaction:
        """`run_id`가 있으면 `X-Agent-Run-Id` — 기록의 출처가 agent가 된다."""
        ...

    async def update(
        self, transaction_id: TransactionId, draft: TransactionDraft, idempotency_key: str
    ) -> Transaction: ...

    async def delete(self, transaction_id: TransactionId, idempotency_key: str) -> None: ...
