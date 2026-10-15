from __future__ import annotations

from dataclasses import dataclass

from .insight_chart import InsightChart


@dataclass(frozen=True, slots=True)
class ReportInsight:
    """리포트의 "눈에 띈 것" — 그림 두 장까지, 문장 세 줄까지(reports.md 3.2).

    둘 다 비었으면 "크게 달라진 것이 없다"는 답이다. 평범한 달에는 조용한 게 맞다.
    """

    charts: tuple[InsightChart, ...] = ()
    highlights: tuple[str, ...] = ()

    @property
    def is_quiet(self) -> bool:
        return not self.charts and not self.highlights
