from __future__ import annotations

from dataclasses import dataclass

from api.domain.entities import Transaction
from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class Outlier:
    """평소 범위를 벗어난 거래 한 건과 그 카테고리의 평소. 숫자를 같이 내야 문장이 근거를 든다."""

    transaction: Transaction
    usual_median: Money
    usual_upper: Money  # 이 금액을 넘었다(domain/rules/usual_range)
