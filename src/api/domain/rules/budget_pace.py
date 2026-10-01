"""예산 페이스 — 지금 속도로 말일에 얼마가 되고, 언제 예산을 넘나.

ui의 메모리 대역이 흉내 내던 계산을 옮겼다. 숫자는 여기서만 낸다 — 화면도 에이전트도
나눗셈을 하지 않는다(README 1장).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from api.domain.values import Money, Period


def elapsed_days(period: Period, today: date) -> int:
    """그 달에서 지나간 날 수. 지난달이면 말일까지, 다음 달이면 0."""
    current = Period.of(today)
    if period < current:
        return period.days
    if period > current:
        return 0
    return today.day


def cumulative(amounts_by_day: Iterable[tuple[int, Money]], through: int) -> tuple[Money, ...]:
    """(날, 금액) 목록을 1일부터 `through`일까지의 누적으로."""
    daily = [Money(0)] * (through + 1)
    for day, amount in amounts_by_day:
        if 1 <= day <= through:
            daily[day] += amount
    running, out = Money(0), []
    for day in range(1, through + 1):
        running += daily[day]
        out.append(running)
    return tuple(out)


def project(spent: Money, elapsed: int, days: int) -> Money:
    """지금 속도로 말일에 닿을 금액. 정수 원으로 내림."""
    if elapsed <= 0:
        return spent
    return Money(spent.amount * days // elapsed)


def crossing_day(series: tuple[Money, ...], limit: Money, days: int) -> int | None:
    """예산을 넘은 날, 아직 안 넘었으면 지금 페이스로 넘을 날. 안 넘으면 None."""
    for day, value in enumerate(series, start=1):
        if value > limit:
            return day
    elapsed = len(series)
    spent = series[-1] if series else Money(0)
    if elapsed >= days or spent.amount <= 0:
        return None
    # 누적 = spent / elapsed * day 가 limit을 넘는 첫 날
    day = limit.amount * elapsed // spent.amount + 1
    return day if day <= days else None


def day_in(period: Period, day: int | None) -> date | None:
    return date(period.year, period.month, day) if day else None
