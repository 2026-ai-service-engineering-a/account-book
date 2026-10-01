"""예산 — `/v1/budgets/status`(get_budget_status)와 `PUT /v1/budgets/{category_id}`(set_budget)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.domain.values import CategoryId, Period
from api.interfaces.schemas import BudgetStatusBody, BudgetWrite
from api.interfaces.services import ServicesDep
from api.interfaces.write_headers import WriteHeadersDep

router = APIRouter(prefix="/v1/budgets")


@router.get("/status")
def status(
    services: ServicesDep,
    period: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
    category_id: str | None = None,
) -> list[BudgetStatusBody]:
    """지출 카테고리 전부. 예산을 정하지 않은 것도 들어 있다."""
    found = services.budgets(Period.parse(period), CategoryId(category_id) if category_id else None)
    return [BudgetStatusBody.of(s) for s in found]


@router.put("/{category_id}")
def set_budget(
    category_id: str, body: BudgetWrite, services: ServicesDep, headers: WriteHeadersDep
) -> Response:
    """이번 달부터 바꾼다. 확인이 언제나 필요하다(README 4장)."""

    def perform(uow: UnitOfWork) -> StoredReply:
        changed = services.set_budget(
            uow, CategoryId(category_id), body.amount(), confirmed=headers.confirmed
        )
        return StoredReply(200, BudgetStatusBody.of(changed).model_dump(mode="json"))

    key_hash = headers.request_hash("PUT", f"/v1/budgets/{category_id}", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return JSONResponse(dict(reply.body or {}), status_code=reply.status_code)
