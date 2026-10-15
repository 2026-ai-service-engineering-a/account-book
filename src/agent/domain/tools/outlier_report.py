from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import TimeRange

from .outlier_line import OutlierLine
from .skipped_line import SkippedLine


@dataclass(frozen=True, slots=True)
class OutlierReport:
    """detect_outliers의 답. "특이한 건이 없다"와 "판정할 수 없다"(skipped)를 가른다."""

    baseline: TimeRange  # 평소를 잰 기간 — 판정 직전 여섯 달
    items: tuple[OutlierLine, ...]
    truncated: bool
    skipped: tuple[SkippedLine, ...]
