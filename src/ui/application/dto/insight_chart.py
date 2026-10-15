from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .insight_point import InsightPoint


@dataclass(frozen=True, slots=True)
class InsightChart:
    """AI가 고른 그림 한 장. 색·축·눈금은 없다 — 렌더러가 정한다(docs/ai/agentic-reports.md 5장)."""

    kind: Literal["bar", "hbar", "line"]
    title: str
    unit: Literal["KRW", "count", "days"]
    points: tuple[InsightPoint, ...]
    note: str = ""
