from __future__ import annotations

from pydantic import BaseModel

from agent.domain.tools import Frequency
from agent.domain.values import Amount


class FrequencyReply(BaseModel):
    """api `GET /v1/stats/frequency`의 응답 본문."""

    count: int
    day_count: int
    avg_gap_days: float | None
    avg_amount: int | None

    def frequency(self) -> Frequency:
        return Frequency(
            count=self.count,
            day_count=self.day_count,
            avg_gap_days=self.avg_gap_days,
            avg_amount=Amount(self.avg_amount) if self.avg_amount is not None else None,
        )
