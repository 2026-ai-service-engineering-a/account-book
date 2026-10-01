from __future__ import annotations

from pydantic import ValidationError

from ui.application.dto import Transaction, TransactionDraft, TransactionFilter, TransactionPage
from ui.application.errors import LedgerUnavailable
from ui.application.values import IdempotencyKey, PageCursor, RunId, TransactionId

from .api_client import ApiClient
from .transaction_page_reply import TransactionPageReply
from .transaction_reply import TransactionReply

# ui에서 나가는 쓰기는 사람이 확인한 것이다 — 폼은 제출이 확인이고(transaction-form.md 4.2),
# 채팅은 확인 카드를 누른 뒤에만 쓴다(chat.md 5장).
_CONFIRMED = {"X-Confirmed-By": "user"}


class HttpTransactionGateway:
    """`/v1/transactions`의 진짜. 메모리 대역(MemoryTransactionGateway)과 같은 포트를 채운다."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def exists_any(self) -> bool:
        page = await self._page({"limit": 1})
        return bool(page.items)

    async def search(
        self, criteria: TransactionFilter, cursor: PageCursor | None = None, limit: int = 50
    ) -> TransactionPage:
        params: dict[str, str | int] = {"period": str(criteria.period), "limit": limit}
        if criteria.direction is not None:
            params["direction"] = criteria.direction.value
        if criteria.category_id is not None:
            params["category_id"] = criteria.category_id
        if criteria.query:
            params["q"] = criteria.query
        if cursor:
            params["cursor"] = cursor
        return await self._page(params)

    async def get(self, transaction_id: TransactionId) -> Transaction:
        response = await self._client.request("GET", f"/v1/transactions/{transaction_id}")
        return _transaction(response.content)

    async def create(
        self, draft: TransactionDraft, idempotency_key: IdempotencyKey, run_id: RunId | None = None
    ) -> Transaction:
        headers = _CONFIRMED | {"Idempotency-Key": idempotency_key}
        if run_id is not None:
            headers["X-Agent-Run-Id"] = run_id
        response = await self._client.request(
            "POST", "/v1/transactions", json=_body(draft), headers=headers
        )
        return _transaction(response.content)

    async def update(
        self,
        transaction_id: TransactionId,
        draft: TransactionDraft,
        idempotency_key: IdempotencyKey,
    ) -> Transaction:
        response = await self._client.request(
            "PATCH",
            f"/v1/transactions/{transaction_id}",
            json=_body(draft),
            headers=_CONFIRMED | {"Idempotency-Key": idempotency_key},
        )
        return _transaction(response.content)

    async def delete(self, transaction_id: TransactionId, idempotency_key: IdempotencyKey) -> None:
        await self._client.request(
            "DELETE",
            f"/v1/transactions/{transaction_id}",
            headers=_CONFIRMED | {"Idempotency-Key": idempotency_key},
        )

    async def _page(self, params: dict[str, str | int]) -> TransactionPage:
        response = await self._client.request("GET", "/v1/transactions", params=params)
        try:
            return TransactionPageReply.model_validate_json(response.content).page()
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error


def _body(draft: TransactionDraft) -> dict[str, object]:
    return {
        "direction": draft.direction.value,
        "amount": draft.amount.amount,
        "occurred_at": draft.occurred_at.isoformat(),
        "category_id": draft.category_id,
        "account_id": draft.account_id,
        "merchant": draft.merchant,
        "memo": draft.memo,
    }


def _transaction(content: bytes) -> Transaction:
    try:
        return TransactionReply.model_validate_json(content).transaction()
    except ValidationError as error:
        raise LedgerUnavailable("모르는 응답 모양") from error
