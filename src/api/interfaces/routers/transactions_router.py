"""`/v1/transactions` — 거래 조회와 쓰기(api-contract 6장). 쓰기는 전부 멱등 키를 지난다."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.application.use_cases.search_transactions import DEFAULT_LIMIT, MAX_LIMIT
from api.domain.values import CategoryId, Direction, TransactionId
from api.interfaces.query_span import period_or_range
from api.interfaces.schemas import TransactionBody, TransactionPageBody, TransactionWrite
from api.interfaces.services import ServicesDep
from api.interfaces.write_headers import WriteHeadersDep

router = APIRouter(prefix="/v1/transactions")


@router.get("")
def search(
    services: ServicesDep,
    period: Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
    start: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    end: Annotated[AwareDatetime | None, Query(alias="to")] = None,
    direction: Literal["expense", "income"] | None = None,
    category_id: str | None = None,
    q: Annotated[str, Query(max_length=100)] = "",
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
) -> TransactionPageBody:
    """`period`(YYYY-MM)는 사용자 타임존의 달, `from`·`to`는 `[from, to)` 경계다. 둘 중 하나만.

    둘 다 없으면 기간 없이 최근 것부터.
    """
    page = services.search(
        period=period_or_range(period, start, end),
        direction=Direction(direction) if direction else None,
        category_id=CategoryId(category_id) if category_id else None,
        text=q,
        cursor=cursor,
        limit=limit,
    )
    return TransactionPageBody.of(page)


@router.get("/{transaction_id}")
def get(transaction_id: str, services: ServicesDep) -> TransactionBody:
    return TransactionBody.of(services.get(TransactionId(transaction_id)))


@router.post("", status_code=201)
def create(body: TransactionWrite, services: ServicesDep, headers: WriteHeadersDep) -> Response:
    def perform(uow: UnitOfWork) -> StoredReply:
        created = services.create(
            uow, body.draft(), run_id=headers.run_id, confirmed=headers.confirmed
        )
        return StoredReply(201, TransactionBody.of(created).model_dump(mode="json"))

    key_hash = headers.request_hash("POST", "/v1/transactions", body)
    return _respond(services.write(headers.idempotency_key, key_hash, perform))


@router.patch("/{transaction_id}")
def update(
    transaction_id: str, body: TransactionWrite, services: ServicesDep, headers: WriteHeadersDep
) -> Response:
    def perform(uow: UnitOfWork) -> StoredReply:
        updated = services.update(
            uow, TransactionId(transaction_id), body.draft(), confirmed=headers.confirmed
        )
        return StoredReply(200, TransactionBody.of(updated).model_dump(mode="json"))

    key_hash = headers.request_hash("PATCH", f"/v1/transactions/{transaction_id}", body)
    return _respond(services.write(headers.idempotency_key, key_hash, perform))


@router.delete("/{transaction_id}", status_code=204)
def delete(transaction_id: str, services: ServicesDep, headers: WriteHeadersDep) -> Response:
    def perform(uow: UnitOfWork) -> StoredReply:
        services.delete(uow, TransactionId(transaction_id), confirmed=headers.confirmed)
        return StoredReply(204)

    key_hash = headers.request_hash("DELETE", f"/v1/transactions/{transaction_id}")
    return _respond(services.write(headers.idempotency_key, key_hash, perform))


def _respond(reply: StoredReply) -> Response:
    if reply.body is None:
        return Response(status_code=reply.status_code)
    return JSONResponse(dict(reply.body), status_code=reply.status_code)
