from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo

from .period_name import PeriodName
from .time_range import TimeRange

MAX_DAYS = 365  # last_n_days의 n, range의 날 수 상한. 3년치를 세는 질문은 받지 않는다


@dataclass(frozen=True, slots=True)
class PeriodSpec:
    """기간 이름과 그 이름이 요구하는 값. 경계는 아직 풀리지 않았다.

    `days`는 `last_n_days`만, `start`는 `month`(그 달 1일)와 `range`만, `end`는 `range`만 쓴다.
    """

    name: PeriodName
    days: int = 0
    start: date | None = None
    end: date | None = None  # range의 마지막 날. 그날도 들어간다

    def __post_init__(self) -> None:
        if (self.days != 0) != (self.name is PeriodName.LAST_N_DAYS):
            raise ValueError("days는 last_n_days만 쓴다")
        if self.name is PeriodName.LAST_N_DAYS and not 1 <= self.days <= MAX_DAYS:
            raise ValueError(f"last_n_days의 n은 1~{MAX_DAYS}다: {self.days}")
        if (self.start is not None) != (self.name in (PeriodName.MONTH, PeriodName.RANGE)):
            raise ValueError("start는 month와 range만 쓴다")
        if (self.end is not None) != (self.name is PeriodName.RANGE):
            raise ValueError("end는 range만 쓴다")
        if self.name is PeriodName.MONTH and self.start is not None and self.start.day != 1:
            raise ValueError("month의 start는 그 달 1일이다")
        if self.start is not None and self.end is not None:
            if self.end < self.start:
                raise ValueError("range의 끝 날짜가 시작보다 앞이다")
            if (self.end - self.start).days + 1 > MAX_DAYS:
                raise ValueError(f"range는 {MAX_DAYS}일까지다")

    def bounds(self, today: date, zone: tzinfo) -> TimeRange:
        """`today`(사용자 타임존의 오늘)를 기준으로 `[시작 00:00, 끝)`을 사용자 타임존으로 낸다.

        주는 월요일에 시작하고, "저번 주"에 오늘은 들어가지 않는다. 진행 중인 기간
        (이번 주·올해·최근 n일)의 끝은 오늘의 끝(내일 00:00)이다.
        """
        first, after = self._days(today)
        return TimeRange(_midnight(first, zone), _midnight(after, zone))

    def _days(self, today: date) -> tuple[date, date]:
        """[첫날, 끝 다음 날) — 날짜로."""
        tomorrow = today + timedelta(days=1)
        monday = today - timedelta(days=today.weekday())
        this_month = today.replace(day=1)
        match self.name:
            case PeriodName.TODAY:
                return today, tomorrow
            case PeriodName.YESTERDAY:
                return today - timedelta(days=1), today
            case PeriodName.THIS_WEEK:
                return monday, tomorrow
            case PeriodName.LAST_WEEK:
                return monday - timedelta(days=7), monday
            case PeriodName.THIS_MONTH:
                return this_month, _next_month(this_month)
            case PeriodName.LAST_MONTH:
                return _previous_month(this_month), this_month
            case PeriodName.THIS_YEAR:
                return date(today.year, 1, 1), tomorrow
            case PeriodName.LAST_N_DAYS:
                # 오늘을 포함한 n일 — "최근 3일"은 그저께·어제·오늘이다
                return today - timedelta(days=self.days - 1), tomorrow
            case PeriodName.MONTH:
                assert self.start is not None  # __post_init__이 보장한다
                return self.start, _next_month(self.start)
            case PeriodName.RANGE:
                assert self.start is not None and self.end is not None
                return self.start, self.end + timedelta(days=1)


def _midnight(day: date, zone: tzinfo) -> datetime:
    return datetime.combine(day, time(0), tzinfo=zone)


def _next_month(first: date) -> date:
    return date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)


def _previous_month(first: date) -> date:
    return date(first.year - 1, 12, 1) if first.month == 1 else date(first.year, first.month - 1, 1)
