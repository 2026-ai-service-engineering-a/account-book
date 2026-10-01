from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .said_day import SaidDay

_DAYS_AGO = {
    SaidDay.UNSPECIFIED: 0,
    SaidDay.TODAY: 0,
    SaidDay.YESTERDAY: 1,
    SaidDay.DAY_BEFORE_YESTERDAY: 2,
}
# 날만 말하고 시각을 말하지 않은 지난날은 한낮으로 둔다. 날짜가 경계를 넘지 않게 하려는 것이다.
_NOON = time(12)


@dataclass(frozen=True, slots=True)
class SaidWhen:
    """한 줄에서 읽은 날짜·시각 표현. `hour`가 None이면 시각을 말하지 않았다."""

    day: SaidDay = SaidDay.UNSPECIFIED
    month: int = 0  # day가 DATE일 때만 뜻이 있다
    day_of_month: int = 0
    hour: int | None = None
    minute: int = 0

    def __post_init__(self) -> None:
        if self.hour is not None and not (0 <= self.hour <= 23 and 0 <= self.minute <= 59):
            raise ValueError(f"시각이 아니다: {self.hour}:{self.minute}")
        if self.day is SaidDay.DATE and not (1 <= self.month <= 12 and self.day_of_month >= 1):
            raise ValueError(f"날짜가 아니다: {self.month}/{self.day_of_month}")

    def resolve(self, now: datetime) -> datetime | None:
        """기준 시각 `now`(aware, 사용자 타임존)로 실제 시각을 정한다.

        말하지 않은 것은 채우지 않는다 — 날짜도 시각도 말하지 않았으면 None이다.
        폼에 이미 있는 값(지금)이 남는다.
        """
        if now.tzinfo is None:
            raise ValueError("기준 시각은 aware여야 한다")
        if self.day is SaidDay.DATE:
            return self._on_date(now)
        if self.day is SaidDay.UNSPECIFIED and self.hour is None:
            return None
        days_ago = _DAYS_AGO[self.day]
        day = (now - timedelta(days=days_ago)).date()
        if self.hour is not None:
            return datetime.combine(day, time(self.hour, self.minute), tzinfo=now.tzinfo)
        if days_ago:
            return datetime.combine(day, _NOON, tzinfo=now.tzinfo)
        return now.replace(second=0, microsecond=0)

    def _on_date(self, now: datetime) -> datetime | None:
        at = _NOON if self.hour is None else time(self.hour, self.minute)
        # 문자에는 연도가 없다. 기준 시각보다 뒤면 작년 것이다(12/31 문자를 1/2에 붙여넣는 경우).
        for year in (now.year, now.year - 1):
            try:
                found = datetime.combine(
                    date(year, self.month, self.day_of_month), at, tzinfo=now.tzinfo
                )
            except ValueError:  # 2/30, 작년이 평년인 2/29
                return None
            if found <= now:
                return found
        return None
