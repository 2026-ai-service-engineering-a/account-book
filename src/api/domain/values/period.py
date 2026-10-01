from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, tzinfo

_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True, slots=True, order=True)
class Period:
    """한 달. `YYYY-MM`으로 오간다. 경계는 사용자 타임존으로 잡는다(development-rules 6.1)."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"달이 아니다: {self.month}")

    @classmethod
    def parse(cls, text: str) -> Period:
        match = _PATTERN.match(text)
        if not match:
            raise ValueError(f"기간은 YYYY-MM이다: {text!r}")
        return cls(int(match.group(1)), int(match.group(2)))

    @classmethod
    def of(cls, day: date) -> Period:
        return cls(day.year, day.month)

    def previous(self) -> Period:
        return Period(self.year - 1, 12) if self.month == 1 else Period(self.year, self.month - 1)

    def next(self) -> Period:
        return Period(self.year + 1, 1) if self.month == 12 else Period(self.year, self.month + 1)

    @property
    def days(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

    def bounds(self, zone: tzinfo) -> tuple[datetime, datetime]:
        """`[1일 0시, 다음 달 1일 0시)` — 끝은 열린 구간이다. `<= 말일 23:59:59`로 자르지 않는다."""
        following = self.next()
        return (
            datetime(self.year, self.month, 1, tzinfo=zone),
            datetime(following.year, following.month, 1, tzinfo=zone),
        )

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
