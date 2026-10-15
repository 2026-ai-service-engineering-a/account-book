from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import TimeRange

from .outlier import Outlier
from .skipped_category import SkippedCategory


@dataclass(frozen=True, slots=True)
class Outliers:
    """`detect_outliers`의 답. 평소 범위를 넘은 정도가 큰 순서이고 상한을 넘으면 `truncated`."""

    baseline: TimeRange  # 평소를 잰 기간 — 판정 기간 직전 여섯 달
    items: tuple[Outlier, ...]
    truncated: bool
    skipped: tuple[SkippedCategory, ...]
