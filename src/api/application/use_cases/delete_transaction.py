from __future__ import annotations

from api.application.ports import UnitOfWork
from api.domain.errors import ConfirmationRequired, TransactionNotFound
from api.domain.values import TransactionId


class DeleteTransaction:
    """거래를 지운다. 되돌릴 수 없어서 **언제나** 확인이 필요하다(api-contract 4장)."""

    def __call__(self, uow: UnitOfWork, transaction_id: TransactionId, *, confirmed: bool) -> None:
        if uow.transactions.get(transaction_id) is None:
            raise TransactionNotFound(transaction_id)
        if not confirmed:
            raise ConfirmationRequired
        uow.transactions.remove(transaction_id)
