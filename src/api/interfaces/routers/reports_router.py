"""집계 — `/v1/summary`(summarize_spending)와 화면용 월간 리포트·페이스.

계산된 숫자만 낸다. 거래 목록을 내려주고 받는 쪽이 더하게 두지 않는다(api-contract 6장).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from api.domain.values import CategoryId, Direction, Period
from api.interfaces.schemas import MonthlyReportBody, PaceBody, TotalsBody
from api.interfaces.services import ServicesDep

router = APIRouter(prefix="/v1")
_PERIOD = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("/summary")
def summary(
    services: ServicesDep,
    period: Annotated[str | None, Query(pattern=_PERIOD)] = None,
    direction: Literal["expense", "income"] | None = None,
    category_id: str | None = None,
    q: Annotated[str, Query(max_length=100)] = "",
) -> TotalsBody:
    """거래 목록과 같은 걸름이다 — 목록과 합계가 다른 거래를 세지 않는다."""
    totals = services.summarize(
        period=Period.parse(period) if period else None,
        direction=Direction(direction) if direction else None,
        category_id=CategoryId(category_id) if category_id else None,
        text=q,
    )
    return TotalsBody.of(totals)


@router.get("/reports/monthly")
def monthly(
    services: ServicesDep, period: Annotated[str, Query(pattern=_PERIOD)]
) -> MonthlyReportBody:
    return MonthlyReportBody.of(services.monthly(Period.parse(period)))


@router.get("/reports/pace")
def pace(
    services: ServicesDep, category_id: str, period: Annotated[str, Query(pattern=_PERIOD)]
) -> PaceBody | None:
    """예산이 없거나 아직 오지 않은 달이면 null."""
    found = services.pace(CategoryId(category_id), Period.parse(period))
    return PaceBody.of(found) if found else None
