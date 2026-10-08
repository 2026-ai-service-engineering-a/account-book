from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Amount


@dataclass(frozen=True, slots=True)
class Frequency:
    """count_frequency의 답. 날은 사용자 타임존의 날이다."""

    count: int
    day_count: int  # 거래가 있던 날 수 — 7건이 5일에 걸쳤는지 하루에 몰렸는지
    avg_gap_days: float | None  # 날이 둘 미만이면 None
    avg_amount: Amount | None  # 0건이면 None — "평균 0원"이 아니다
