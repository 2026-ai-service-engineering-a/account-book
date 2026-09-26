from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from ui.application.dto import PaceSeries

from .nice_scale import axis_label, nice_step, scale_top

_LEFT, _RIGHT, _BOTTOM, _TOP = 54, 600, 176, 22


class _Tick(TypedDict):
    x: float
    label: str


class _Grid(TypedDict):
    y: float
    label: str


@dataclass(frozen=True, slots=True)
class PaceChart:
    """누적 지출과 예산 선. *언제* 넘는지는 문장보다 선이 빠르다(reports.md 6장)."""

    title: str
    grid: tuple[_Grid, ...]
    actual: str  # polyline points
    projection: str | None  # 점선. 달이 끝났으면 없다
    today_x: float
    today_y: float
    today_value: str
    budget_y: float
    budget_label: str
    over_x: float | None
    over_title: str
    ticks: tuple[_Tick, ...]

    @classmethod
    def build(cls, series: PaceSeries) -> PaceChart:
        days = series.days_in_month
        spent = series.cumulative[-1] if series.cumulative else 0
        peak = max(series.limit, series.projected, spent)
        step = nice_step(peak)
        top = scale_top(peak, step)

        def x(day: int) -> float:
            return round(_LEFT + (day - 1) / max(days - 1, 1) * (_RIGHT - _LEFT), 1)

        def y(value: int) -> float:
            return round(_BOTTOM - value / top * (_BOTTOM - _TOP), 1)

        elapsed = len(series.cumulative)
        points = " ".join(f"{x(d)},{y(v)}" for d, v in enumerate(series.cumulative, start=1))
        projection = (
            f"{x(elapsed)},{y(spent)} {x(days)},{y(series.projected)}" if elapsed < days else None
        )
        over = series.over_on
        tick_days = sorted({1, 10, 20, days, elapsed} - _crowded(elapsed, days))
        return cls(
            title=_title(series),
            grid=tuple(_Grid(y=y(v), label=axis_label(v)) for v in range(0, top + 1, step)),
            actual=points,
            projection=projection,
            today_x=x(elapsed),
            today_y=y(spent),
            today_value=f"{spent:,}",
            budget_y=y(series.limit),
            budget_label=f"예산 {series.limit:,}",
            over_x=x(over.day) if over else None,
            over_title=f"{over.month}/{over.day} 예산 초과" if over else "",
            ticks=tuple(_Tick(x=x(d), label=f"{d}일") for d in tick_days),
        )


def _crowded(elapsed: int, days: int) -> set[int]:
    """오늘 눈금과 겹치는 고정 눈금은 뺀다. 글자가 포개지면 둘 다 안 읽힌다."""
    return {d for d in (1, 10, 20, days) if d != elapsed and abs(d - elapsed) < 3}


def _title(series: PaceSeries) -> str:
    name = series.category.name
    if series.over_on is None:
        return f"{name} — 이 페이스면 예산 안이다"
    if series.cumulative and series.cumulative[-1] > series.limit:
        return f"{name} — 예산을 넘었다"
    return f"{name} — 이 페이스면 예산을 넘는다"
