from __future__ import annotations

from collections.abc import Callable

from api.application.ports import UnitOfWork
from api.domain.entities import Transaction
from api.domain.errors import TransactionNotFound
from api.domain.values import TransactionId


class GetTransaction:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, transaction_id: TransactionId) -> Transaction:
        with self._unit_of_work() as uow:
            found = uow.transactions.get(transaction_id)
        if found is None:
            raise TransactionNotFound(transaction_id)
        return found
