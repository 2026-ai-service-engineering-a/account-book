from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """검색이 계산한 신뢰도. 0~1이다 — "0.8인지 80인지"를 경계에서 한 번만 막는다
    (docs/ai/README.md 3장). 모델이 스스로 말한 확신과는 다른 물건이다."""

    value: float

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not 0.0 <= self.value <= 1.0:
            raise ValueError(f"신뢰도는 0~1이다: {self.value!r}")
