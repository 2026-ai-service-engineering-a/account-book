from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from api.domain.entities import Category
from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class PaceSeries:
    """한 카테고리의 날짜별 누적 지출. 리포트의 페이스 차트가 그린다."""

    category: Category
    limit: Money
    cumulative: tuple[Money, ...]  # 1일부터 오늘(또는 말일)까지
    days_in_month: int
    projected: Money
    over_on: date | None
