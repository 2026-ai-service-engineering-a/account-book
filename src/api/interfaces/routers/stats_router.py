"""기간 집계 — `/v1/stats/frequency`(count_frequency)와 `/v1/stats/compare`(compare_periods).

기간은 이름이 아니라 경계로 받는다. `from`·`to`는 오프셋이 붙은 ISO 8601 시각이고 `[from, to)`다.
naive 시각은 422다 — 어느 타임존의 자정인지 모르는 경계로 세지 않는다.
"저번 주"를 날짜로 푸는 일은 부르는 쪽이 사용자 타임존으로 한다(ai/chat-analytics.md 5장).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import AwareDatetime

from api.domain.values import CategoryId, Direction
from api.interfaces.query_span import time_range
from api.interfaces.schemas import FrequencyBody, PeriodChangeBody
from api.interfaces.services import ServicesDep

router = APIRouter(prefix="/v1/stats")


@router.get("/frequency")
def frequency(
    services: ServicesDep,
    start: Annotated[AwareDatetime, Query(alias="from")],
    end: Annotated[AwareDatetime, Query(alias="to")],
    direction: Literal["expense", "income"] = "expense",
    category_id: str | None = None,
    q: Annotated[str, Query(max_length=100)] = "",
) -> FrequencyBody:
    """걸름은 `/v1/summary`와 같다. 방향의 기본만 지출이다."""
    found = services.frequency(
        time_range(start, end, "to"),
        direction=Direction(direction),
        category_id=CategoryId(category_id) if category_id else None,
        text=q,
    )
    return FrequencyBody.of(found)


@router.get("/compare")
def compare(
    services: ServicesDep,
    a_from: AwareDatetime,
    a_to: AwareDatetime,
    b_from: AwareDatetime,
    b_to: AwareDatetime,
    category_id: str | None = None,
) -> list[PeriodChangeBody]:
    """지출 카테고리별 a 합·b 합·증감. b가 큰 순서."""
    found = services.compare(
        time_range(a_from, a_to, "a_to"),
        time_range(b_from, b_to, "b_to"),
        CategoryId(category_id) if category_id else None,
    )
    return [PeriodChangeBody.of(change) for change in found]
