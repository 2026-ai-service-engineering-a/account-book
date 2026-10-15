from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InsightPoint:
    """AI 차트의 점 하나. 값은 agent가 도구 결과에서 옮긴 것이다 — 화면은 그리기만 한다."""

    label: str
    value: int | float
    annotated: bool = False  # 숫자를 직접 달 점
