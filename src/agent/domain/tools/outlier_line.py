from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent.domain.values import Amount, CategoryId


@dataclass(frozen=True, slots=True)
class OutlierLine:
    """평소 범위를 넘은 거래 한 줄과 그 카테고리의 평소. 가맹점은 사용자 데이터다."""

    id: str
    occurred_at: datetime
    category_id: CategoryId
    merchant: str
    amount: Amount
    usual_median: Amount
    usual_upper: Amount  # 이 금액을 넘었다 — 지난 여섯 달의 어느 거래보다도 크다
