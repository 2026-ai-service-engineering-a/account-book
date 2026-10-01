from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from ui.application.dto import BudgetStatus, Period
from ui.application.errors import LedgerUnavailable
from ui.application.values import CategoryId, IdempotencyKey, Money

from .api_client import ApiClient
from .budget_status_reply import BudgetStatusReply

_STATUSES = TypeAdapter(list[BudgetStatusReply])


class HttpBudgetGateway:
    """예산의 진짜 — api의 `/v1/budgets/*`. 예산은 바꾼 달부터 이어진다."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def statuses(self, period: Period) -> tuple[BudgetStatus, ...]:
        return await self._statuses({"period": str(period)})

    async def status(self, category_id: CategoryId, period: Period) -> BudgetStatus:
        found = await self._statuses({"period": str(period), "category_id": category_id})
        if not found:
            raise LedgerUnavailable("지출 카테고리가 아니다")
        return found[0]

    async def set_limit(
        self, category_id: CategoryId, amount: Money | None, idempotency_key: IdempotencyKey
    ) -> BudgetStatus:
        # 예산 설정은 언제나 확인이 필요하다(README 4장). 화면의 저장 버튼이 그 확인이다.
        headers = {"Idempotency-Key": idempotency_key, "X-Confirmed-By": "user"}
        body: dict[str, object] = {"limit_amount": amount.amount if amount else None}
        response = await self._client.request(
            "PUT", f"/v1/budgets/{category_id}", json=body, headers=headers
        )
        try:
            return BudgetStatusReply.model_validate_json(response.content).status()
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error

    async def _statuses(self, params: dict[str, str | int]) -> tuple[BudgetStatus, ...]:
        response = await self._client.request("GET", "/v1/budgets/status", params=params)
        try:
            return tuple(r.status() for r in _STATUSES.validate_json(response.content))
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
