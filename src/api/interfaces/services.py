from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from api.application.ports import DatabaseProbe
from api.application.use_cases import (
    CreateTransaction,
    DeleteTransaction,
    GetTransaction,
    IdempotentWrite,
    ListCatalog,
    SearchTransactions,
    UpdateTransaction,
)


@dataclass(frozen=True, slots=True)
class Services:
    """라우터가 쓰는 유스케이스 묶음. 무엇으로 조립했는지는 main.py만 안다."""

    database: DatabaseProbe
    write: IdempotentWrite
    create: CreateTransaction
    update: UpdateTransaction
    delete: DeleteTransaction
    get: GetTransaction
    search: SearchTransactions
    catalog: ListCatalog


def get_services(request: Request) -> Services:
    services = request.app.state.services
    if not isinstance(services, Services):
        raise RuntimeError("app.state.services가 조립되지 않았다")
    return services


ServicesDep = Annotated[Services, Depends(get_services)]
