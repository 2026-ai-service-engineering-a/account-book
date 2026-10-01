"""카테고리와 결제수단 — 화면의 셀렉트가 쓴다. 도구가 아니라 기준 데이터다."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from api.domain.values import Direction
from api.interfaces.schemas import AccountBody, CategoryBody
from api.interfaces.services import ServicesDep

router = APIRouter(prefix="/v1")


@router.get("/categories")
def categories(
    services: ServicesDep, direction: Literal["expense", "income"] | None = None
) -> list[CategoryBody]:
    found = services.catalog.categories(Direction(direction) if direction else None)
    return [CategoryBody.of(c) for c in found]


@router.get("/accounts")
def accounts(services: ServicesDep) -> list[AccountBody]:
    return [AccountBody.of(a) for a in services.catalog.accounts()]
