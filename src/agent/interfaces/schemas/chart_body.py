from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agent.application.dto import Chart

from .chart_point_body import ChartPointBody


class ChartBody(BaseModel):
    """그릴 차트 하나. 색·축·눈금은 없다 — ui의 렌더러가 정한다(agentic-reports 5장)."""

    kind: Literal["bar", "hbar", "line"]
    title: str
    unit: Literal["KRW", "count", "days"]
    note: str
    points: list[ChartPointBody]

    @classmethod
    def of(cls, chart: Chart) -> ChartBody:
        return cls.model_validate(
            {
                "kind": chart.kind,
                "title": chart.title,
                "unit": chart.unit,
                "note": chart.note,
                "points": [ChartPointBody.of(p) for p in chart.points],
            }
        )
