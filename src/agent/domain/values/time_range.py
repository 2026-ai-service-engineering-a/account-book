from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class TimeRange:
    """`[start, end)` — api에 넘기는 기간 경계. 끝은 열린 구간이다(development-rules 6.1)."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("기간 경계는 aware여야 한다")
        if self.start >= self.end:
            raise ValueError("기간의 끝은 시작보다 뒤여야 한다")

    def first(self, length: timedelta) -> TimeRange:
        """앞에서부터 `length`만큼. 원래 기간보다 길면 그대로다."""
        return TimeRange(self.start, min(self.end, self.start + length))
