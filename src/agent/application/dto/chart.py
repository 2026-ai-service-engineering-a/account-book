from __future__ import annotations

from dataclasses import dataclass

from .chart_point import ChartPoint


@dataclass(frozen=True, slots=True)
class Chart:
    """검증을 지나 값이 채워진 차트. 색·축·눈금은 없다 — 렌더러가 정한다(agentic-reports 5장)."""

    kind: str  # bar · hbar · line
    title: str
    unit: str  # KRW · count · days
    points: tuple[ChartPoint, ...]
    note: str = ""
