from __future__ import annotations

from enum import StrEnum


class SkipReason(StrEnum):
    """평소 범위를 판정하지 않은 이유. "특이한 건이 없다"와 "판정할 수 없다"는 다른 답이다."""

    SHORT_HISTORY = "short_history"  # 첫 거래가 평소의 시작보다 늦다 — 여섯 달이 안 됐다
    TOO_FEW = "too_few"  # 여섯 달은 됐지만 평소 기간의 거래가 너무 적다
