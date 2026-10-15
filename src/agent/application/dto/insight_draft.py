from __future__ import annotations

from dataclasses import dataclass

from .chart_spec import ChartSpec
from .highlight_draft import HighlightDraft


@dataclass(frozen=True, slots=True)
class InsightDraft:
    """조립 호출(LLM 2)의 답 — 검증 전의 차트 선언과 문장."""

    charts: tuple[ChartSpec, ...]
    highlights: tuple[HighlightDraft, ...]
