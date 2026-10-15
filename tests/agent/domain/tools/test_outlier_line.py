from __future__ import annotations

from datetime import UTC, datetime

from agent.domain.tools import OutlierLine
from agent.domain.values import Amount, CategoryId


def big_one() -> OutlierLine:
    return OutlierLine(
        "t1",
        datetime(2026, 9, 14, 6, tzinfo=UTC),
        CategoryId("living"),
        "전자랜드",
        Amount(890_000),
        Amount(52_000),
        Amount(89_000),
    )


def test_carries_the_usual_next_to_the_amount():
    line = big_one()
    assert line.amount.amount > line.usual_upper.amount > line.usual_median.amount
