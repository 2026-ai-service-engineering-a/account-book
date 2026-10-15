from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from api.domain.values import CategoryId, Money


@dataclass(frozen=True, slots=True)
class CategoryBaseline:
    """한 카테고리의 평소 — 기준 기간 거래의 중앙값·MAD·최댓값·건수와, 그 방향의 첫 거래 시각.

    기준 기간에 거래가 없으면 건수 0, 중앙값·MAD·최댓값 0이다. 판정 기간 전에 거래가 하나도 없으면
    `first_at`이 None이다.
    """

    category_id: CategoryId
    median: Money
    mad: Money  # 중앙값에서 떨어진 거리의 중앙값
    largest: Money  # 기준 기간의 가장 큰 거래
    count: int
    first_at: datetime | None
