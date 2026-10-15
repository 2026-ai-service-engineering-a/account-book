from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .chart import Chart
from .insight_stop import InsightStop
from .tool_step import ToolStep


@dataclass(frozen=True, slots=True)
class Insight:
    """리포트의 AI 영역. 차트도 문장도 없으면 화면은 그 영역을 그리지 않는다(agentic-reports 7장).

    `steps`·`whys`·`model_calls`는 감사 로그의 몫이다.
    `whys`는 계획 단계의 call_id → 모델이 쓴 이유.
    """

    stop: InsightStop
    charts: tuple[Chart, ...] = ()
    highlights: tuple[str, ...] = ()
    steps: tuple[ToolStep, ...] = ()
    whys: Mapping[str, str] = field(default_factory=dict)
    model_calls: int = 0
    replanned: bool = False
