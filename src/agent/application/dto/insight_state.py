from __future__ import annotations

from dataclasses import dataclass, field

from .chart import Chart
from .insight import Insight
from .insight_stop import InsightStop
from .tool_step import ToolStep


@dataclass
class InsightState:
    """리포트 실행 하나의 상태(채팅의 LoopState에 해당). 실행 안에서만 바뀐다 — 유스케이스는
    요청들이 나눠 쓰므로 세는 값을 거기 두지 않는다."""

    steps: list[ToolStep] = field(default_factory=list)
    whys: dict[str, str] = field(default_factory=dict)  # 계획 단계의 call_id → 이유
    charts: tuple[Chart, ...] = ()
    highlights: tuple[str, ...] = ()
    model_calls: int = 0
    replanned: bool = False

    def end(self, stop: InsightStop) -> Insight:
        return Insight(
            stop,
            self.charts,
            self.highlights,
            tuple(self.steps),
            dict(self.whys),
            self.model_calls,
            self.replanned,
        )
