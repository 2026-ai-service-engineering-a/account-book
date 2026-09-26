from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date

_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True, slots=True, order=True)
class Period:
    """한 달. `YYYY-MM`으로 URL에 오간다."""

    year: int
    month: int

    @classmethod
    def parse(cls, text: str) -> Period | None:
        match = _PATTERN.match(text)
        if not match:
            return None
        year, month = int(match.group(1)), int(match.group(2))
        return cls(year, month) if 1 <= month <= 12 else None

    @classmethod
    def of(cls, day: date) -> Period:
        return cls(day.year, day.month)

    def previous(self) -> Period:
        return Period(self.year - 1, 12) if self.month == 1 else Period(self.year, self.month - 1)

    def next(self) -> Period:
        return Period(self.year + 1, 1) if self.month == 12 else Period(self.year, self.month + 1)

    def contains(self, day: date) -> bool:
        return day.year == self.year and day.month == self.month

    @property
    def days(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def label(self) -> str:
        return f"{self.year}년 {self.month}월"

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
