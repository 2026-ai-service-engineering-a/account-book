from __future__ import annotations

from pydantic import BaseModel

from agent.application.dto import Insight

from .chart_body import ChartBody


class InsightResponse(BaseModel):
    """리포트의 AI 영역 — 차트 두 장까지, 문장 세 줄까지. 둘 다 비었으면 그 영역을 그리지 않는다.

    비어 있는 것도 실패가 아니라 답이다. 평범한 달에는 조용한 게 맞다(agentic-reports 9장).
    """

    charts: list[ChartBody]
    highlights: list[str]

    @classmethod
    def of(cls, insight: Insight) -> InsightResponse:
        return cls(
            charts=[ChartBody.of(c) for c in insight.charts], highlights=list(insight.highlights)
        )
