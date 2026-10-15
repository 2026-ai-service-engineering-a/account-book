from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChartPoint:
    """차트의 점 하나. 값은 코드가 도구 결과에서 옮긴 것이다 — 모델이 쓴 숫자가 아니다."""

    label: str
    value: int | float
    annotated: bool = False  # 숫자를 직접 달 지점
