"""차트 축 눈금. 사람이 읽기 좋은 값(1, 2, 5에 10의 거듭제곱)으로 끊는다."""

from __future__ import annotations

import math


def nice_step(peak: int, ticks: int = 3) -> int:
    if peak <= 0:
        return 1
    raw = peak / ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiple in (1, 2, 5, 10):
        if multiple * magnitude >= raw:
            return max(int(multiple * magnitude), 1)
    return int(10 * magnitude)


def scale_top(peak: int, step: int) -> int:
    return max(step * math.ceil(peak / step), step)


def axis_label(value: int) -> str:
    if value and value % 10_000 == 0:
        return f"{value // 10_000:,}만"
    return f"{value:,}"
