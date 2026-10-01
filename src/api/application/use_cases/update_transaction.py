from __future__ import annotations

import dataclasses

from api.application.dto import TransactionDraft
from api.application.ports import UnitOfWork
from api.domain.entities import Transaction
from api.domain.errors import ConfirmationRequired, TransactionNotFound
from api.domain.values import Money, TransactionId

from .draft_check import check_draft


class UpdateTransaction:
    """거래의 값을 바꾼다. 출처(source·run_id)는 그대로 둔다.

    누가 처음 넣었는지는 고쳐도 바뀌지 않는다.
    """

    def __init__(self, confirm_threshold: Money) -> None:
        self._threshold = confirm_threshold

    def __call__(
        self,
        uow: UnitOfWork,
        transaction_id: TransactionId,
        draft: TransactionDraft,
        *,
        confirmed: bool,
    ) -> Transaction:
        existing = uow.transactions.get(transaction_id)
        if existing is None:
            raise TransactionNotFound(transaction_id)
        check_draft(draft, uow.catalog)
        if draft.amount >= self._threshold and not confirmed:
            raise ConfirmationRequired
        updated = dataclasses.replace(
            existing,
            direction=draft.direction,
            amount=draft.amount,
            occurred_at=draft.occurred_at,
            category_id=draft.category_id,
            account_id=draft.account_id,
            merchant=draft.merchant.strip(),
            memo=draft.memo.strip(),
        )
        uow.transactions.replace(updated)
        return updated
