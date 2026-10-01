from __future__ import annotations

import uuid
from collections.abc import Callable

from api.application.dto import TransactionDraft
from api.application.ports import UnitOfWork
from api.domain.entities import Transaction
from api.domain.errors import ConfirmationRequired
from api.domain.values import Money, Source, TransactionId

from .draft_check import check_draft


def _new_id() -> TransactionId:
    return TransactionId(str(uuid.uuid4()))


class CreateTransaction:
    """거래 한 건을 넣는다. 커밋은 부르는 쪽(멱등 쓰기)이 한다 — 키와 같은 트랜잭션이다."""

    def __init__(
        self, confirm_threshold: Money, new_id: Callable[[], TransactionId] = _new_id
    ) -> None:
        self._threshold = confirm_threshold
        self._new_id = new_id

    def __call__(
        self, uow: UnitOfWork, draft: TransactionDraft, *, run_id: str | None, confirmed: bool
    ) -> Transaction:
        """`run_id`가 있으면 에이전트가 넣은 것이다(source=agent). 검사 → 확인 → 쓰기 순서다 —
        고칠 것이 있으면 확인을 묻기 전에 알려 준다."""
        check_draft(draft, uow.catalog)
        if draft.amount >= self._threshold and not confirmed:
            raise ConfirmationRequired
        created = Transaction(
            id=self._new_id(),
            direction=draft.direction,
            amount=draft.amount,
            occurred_at=draft.occurred_at,
            category_id=draft.category_id,
            account_id=draft.account_id,
            merchant=draft.merchant.strip(),
            memo=draft.memo.strip(),
            source=Source.AGENT if run_id else Source.MANUAL,
            run_id=run_id,
        )
        uow.transactions.add(created)
        return created
