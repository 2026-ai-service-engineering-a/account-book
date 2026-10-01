from __future__ import annotations

from typing import Protocol

from api.application.dto import TransactionPage, TransactionQuery
from api.domain.entities import Transaction
from api.domain.values import TransactionId


class TransactionRepository(Protocol):
    """거래 저장소. 최근 것부터 낸다 — (occurred_at, id) 내림차순."""

    def get(self, transaction_id: TransactionId) -> Transaction | None: ...

    def search(self, query: TransactionQuery) -> TransactionPage: ...

    def add(self, transaction: Transaction) -> None: ...

    def replace(self, transaction: Transaction) -> None: ...

    def remove(self, transaction_id: TransactionId) -> None: ...
