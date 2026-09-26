from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypedDict

from ui.application.dto import MonthTotal

from .nice_scale import axis_label, nice_step, scale_top

_LEFT, _RIGHT, _BASE, _TOP, _BAR, _RADIUS = 54, 620, 172, 16, 22, 4


class _Grid(TypedDict):
    y: float
    label: str


class _Group(TypedDict):
    label: str
    center: float
    expense_path: str
    income_path: str
    expense_title: str
    income_title: str


@dataclass(frozen=True, slots=True)
class MonthBarChart:
    """ "여섯 달" — 월별 지출·수입. 둘 다 원이라 축은 하나다(reports.md 3.1)."""

    grid: tuple[_Grid, ...]
    groups: tuple[_Group, ...]

    @classmethod
    def build(cls, months: Sequence[MonthTotal]) -> MonthBarChart:
        peak = max((max(m.expense.amount, m.income.amount) for m in months), default=0)
        step = nice_step(peak)
        top = scale_top(peak, step)

        def y(value: int) -> float:
            return _BASE - value / top * (_BASE - _TOP)

        width = (_RIGHT - _LEFT) / max(len(months), 1)
        groups = []
        for index, month in enumerate(months):
            center = _LEFT + width * (index + 0.5)
            name = f"{month.period.month}월"
            groups.append(
                _Group(
                    label=name,
                    center=round(center, 1),
                    expense_path=_top_rounded(center - _BAR - 1, y(month.expense.amount)),
                    income_path=_top_rounded(center + 1, y(month.income.amount)),
                    expense_title=f"{name} 지출 {month.expense:,}원",
                    income_title=f"{name} 수입 {month.income:,}원",
                )
            )
        grid = tuple(_Grid(y=round(y(v), 1), label=axis_label(v)) for v in range(0, top + 1, step))
        return cls(grid=grid, groups=tuple(groups))


def _top_rounded(left: float, top: float) -> str:
    right = left + _BAR
    if _BASE - top < _RADIUS:
        return f"M{left:.1f},{_BASE} V{top:.1f} H{right:.1f} V{_BASE} Z"
    return (
        f"M{left:.1f},{_BASE} V{top + _RADIUS:.1f} "
        f"A{_RADIUS},{_RADIUS} 0 0 1 {left + _RADIUS:.1f},{top:.1f} H{right - _RADIUS:.1f} "
        f"A{_RADIUS},{_RADIUS} 0 0 1 {right:.1f},{top + _RADIUS:.1f} V{_BASE} Z"
    )
