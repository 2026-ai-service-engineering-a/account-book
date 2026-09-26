"""예산 페이스 계산. api가 할 일을 대역이 흉내 낸다 — 화면은 이 파일을 모른다."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from ui.application.dto import Period


def elapsed_days(period: Period, today: date) -> int:
    """그 달에서 지나간 날 수. 지난달이면 말일까지, 다음 달이면 0."""
    current = Period.of(today)
    if period < current:
        return period.days
    if period > current:
        return 0
    return today.day


def cumulative(amounts_by_day: Iterable[tuple[int, int]], through: int) -> tuple[int, ...]:
    """(날, 금액) 목록을 1일부터 `through`일까지의 누적으로."""
    daily = [0] * (through + 1)
    for day, amount in amounts_by_day:
        if 1 <= day <= through:
            daily[day] += amount
    running, out = 0, []
    for day in range(1, through + 1):
        running += daily[day]
        out.append(running)
    return tuple(out)


def project(spent: int, elapsed: int, days: int) -> int:
    """지금 속도로 말일에 닿을 금액. 정수 원으로 내림."""
    if elapsed <= 0:
        return spent
    return spent * days // elapsed


def crossing_day(series: tuple[int, ...], limit: int, days: int) -> int | None:
    """예산을 넘은 날, 아직 안 넘었으면 지금 페이스로 넘을 날. 안 넘으면 None."""
    for day, value in enumerate(series, start=1):
        if value > limit:
            return day
    elapsed = len(series)
    spent = series[-1] if series else 0
    if elapsed >= days or spent <= 0:
        return None
    day = limit * elapsed // spent + 1  # 누적 = spent / elapsed * day 가 limit을 넘는 첫 날
    return day if day <= days else None


def day_in(period: Period, day: int | None) -> date | None:
    return date(period.year, period.month, day) if day else None
