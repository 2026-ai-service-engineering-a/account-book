from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class Frequency:
    """기간 안에 몇 번, 며칠에 걸쳐. "날"은 사용자 타임존의 날이다.

    건수와 날 수를 같이 낸다 — 카페 7건이 5일에 걸쳤는지 하루에 몰렸는지는 다른
    이야기다(ai/chat-analytics.md 3.1).
    """

    count: int
    day_count: int
    avg_gap_days: float | None  # 거래가 있던 날 사이의 평균 간격. 날이 둘 미만이면 None
    avg_amount: Money | None  # 회당 평균, 원 단위 반올림. 0건이면 None — "평균 0원"이 아니다
