from __future__ import annotations

from pydantic import BaseModel

from .amounts import amount


class FrequencyReply(BaseModel):
    """api `GET /v1/stats/frequency`의 응답 본문."""

    count: int
    day_count: int
    avg_gap_days: float | None
    avg_amount: int | None  # 0건이면 None — "평균 0원"이 아니다

    def row(self) -> dict[str, object]:
        return {
            "count": self.count,
            "day_count": self.day_count,
            "avg_gap_days": self.avg_gap_days,
            "avg_amount": amount(self.avg_amount),
        }
