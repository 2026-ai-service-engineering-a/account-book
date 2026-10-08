from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import Frequency


class FrequencyBody(BaseModel):
    """건수·날 수·날 사이 평균 간격(일)·회당 평균(정수 원). 0건이면 평균 둘은 null."""

    count: int
    day_count: int
    avg_gap_days: float | None
    avg_amount: int | None

    @classmethod
    def of(cls, found: Frequency) -> FrequencyBody:
        return cls(
            count=found.count,
            day_count=found.day_count,
            avg_gap_days=found.avg_gap_days,
            avg_amount=found.avg_amount.amount if found.avg_amount is not None else None,
        )
