from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypedDict

_LEFT, _WIDTH, _TOP, _PITCH, _HEIGHT, _RADIUS = 54, 400, 6, 30, 18, 4


class _Bar(TypedDict):
    label: str
    title: str
    path: str
    text_y: int
    value_x: float
    value: str


@dataclass(frozen=True, slots=True)
class CategoryBarChart:
    """ "어디에 썼나" — 카테고리 가로 막대. 큰 순서, 계열 하나라 범례가 없다."""

    height: int
    bars: tuple[_Bar, ...]

    @classmethod
    def build(cls, rows: Sequence[tuple[str, int]]) -> CategoryBarChart:
        peak = max((value for _, value in rows), default=0) or 1
        bars = []
        for index, (label, value) in enumerate(rows):
            top = _TOP + index * _PITCH
            end = _LEFT + max(value / peak * _WIDTH, 2)
            bars.append(
                _Bar(
                    label=label,
                    title=f"{label} {value:,}원",
                    path=_right_rounded(top, end),
                    text_y=top + 13,
                    value_x=round(end + 8, 1),
                    value=f"{value:,}",
                )
            )
        return cls(height=_TOP * 2 + len(rows) * _PITCH, bars=tuple(bars))


def _right_rounded(top: int, end: float) -> str:
    bottom = top + _HEIGHT
    if end - _LEFT < _RADIUS * 2:
        return f"M{_LEFT},{top} H{end:.1f} V{bottom} H{_LEFT} Z"
    inner = end - _RADIUS
    return (
        f"M{_LEFT},{top} H{inner:.1f} A{_RADIUS},{_RADIUS} 0 0 1 {end:.1f},{top + _RADIUS} "
        f"V{bottom - _RADIUS} A{_RADIUS},{_RADIUS} 0 0 1 {inner:.1f},{bottom} H{_LEFT} Z"
    )
