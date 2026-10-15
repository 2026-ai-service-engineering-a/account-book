"""AI가 고른 그림을 인라인 SVG의 좌표로(reports.md 3.1, docs/ai/agentic-reports.md 5장).

스펙에는 색·축·눈금이 없다 — 여기서 정한다. 계열은 하나라 범례를 두지 않고 색도 하나다.
축은 하나, 0선은 실선 하나. 숫자는 `annotated` 점에만 단다 — 전부 달면 아무것도 읽히지 않는다.
값이 음수(증감)일 수 있어 0선을 기준으로 그린다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from ui.application.dto import InsightChart

_LEFT, _RIGHT, _TOP, _PITCH, _BAR = 132, 600, 6, 30, 18  # 가로 막대
_PLOT_TOP, _PLOT_HEIGHT, _LABEL_Y = 18, 160, 200  # 세로 막대·선


class _Mark(TypedDict):
    label: str
    title: str  # 마우스를 올리면 보이는 정확한 값
    x: float
    y: float
    w: float
    h: float
    label_x: float
    label_y: float
    value_x: float
    value_y: float
    value: str  # 단 숫자. annotated가 아니면 빈 글자


@dataclass(frozen=True, slots=True)
class InsightChartView:
    kind: str
    title: str
    note: str
    height: int
    zero: float  # 0선의 좌표 — 가로 막대는 x, 세로 막대·선은 y
    marks: tuple[_Mark, ...]
    line: str  # 선 그래프의 points. 다른 모양은 비어 있다

    @classmethod
    def build(cls, chart: InsightChart) -> InsightChartView:
        values = [p.value for p in chart.points]
        low, high = min(0, *values), max(0, *values)
        span = (high - low) or 1
        marks: list[_Mark] = []
        if chart.kind == "hbar":
            width = _RIGHT - _LEFT
            zero = _LEFT + (-low) / span * width
            for index, point in enumerate(chart.points):
                end = _LEFT + (point.value - low) / span * width
                top = _TOP + index * _PITCH
                marks.append(_mark(chart.unit, point.label, point.value, point.annotated,
                    x=min(zero, end), y=top, w=max(abs(end - zero), 2), h=_BAR,
                    label_x=_LEFT - 8, label_y=top + 13,
                    value_x=max(zero, end) + 6, value_y=top + 13))  # fmt: skip
            height = _TOP * 2 + len(chart.points) * _PITCH
            return cls(chart.kind, chart.title, chart.note, height, zero, tuple(marks), "")
        pitch = (_RIGHT - 40) / len(chart.points)
        zero = _PLOT_TOP + high / span * _PLOT_HEIGHT
        for index, point in enumerate(chart.points):
            center = 40 + pitch * (index + 0.5)
            level = _PLOT_TOP + (high - point.value) / span * _PLOT_HEIGHT
            bar = min(pitch * 0.6, 48)
            marks.append(_mark(chart.unit, point.label, point.value, point.annotated,
                x=center - bar / 2, y=min(zero, level), w=bar, h=max(abs(zero - level), 2),
                label_x=center, label_y=_LABEL_Y,
                value_x=center, value_y=min(zero, level) - 6))  # fmt: skip
        line = " ".join(f"{m['value_x']:.1f},{m['value_y'] + 6:.1f}" for m in marks)
        points = line if chart.kind == "line" else ""
        return cls(chart.kind, chart.title, chart.note, _LABEL_Y + 10, zero, tuple(marks), points)


def _mark(unit: str, label: str, value: float, annotated: bool, **at: float) -> _Mark:
    text = _format(unit, value)
    return _Mark(
        label=label,
        title=f"{label} {text}",
        value=text if annotated else "",
        x=at["x"], y=at["y"], w=at["w"], h=at["h"],
        label_x=at["label_x"], label_y=at["label_y"],
        value_x=at["value_x"], value_y=at["value_y"],
    )  # fmt: skip


def _format(unit: str, value: float) -> str:
    if unit == "KRW":
        return f"{value:,.0f}원"
    if unit == "count":
        return f"{value:,.0f}건"
    return f"{value:,.1f}일".replace(".0일", "일")
