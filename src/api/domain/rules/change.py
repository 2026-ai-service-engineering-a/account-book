"""두 금액 사이의 증감.

월간 리포트와 기간 비교가 같은 식을 쓴다 — 같은 계산이 두 군데 생기지 않게.
"""

from __future__ import annotations

from api.domain.values import Money


def percent(before: Money, after: Money) -> int | None:
    """`before` 대비 증감 비율(절댓값, 정수 %). 방향은 증감 금액의 부호가 말한다.

    `before`가 0이면 None이다. 0에서 늘어난 것에는 비율이 없다.
    """
    if not before.amount:
        return None
    return round(abs(after.amount - before.amount) * 100 / before.amount)
