from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClassifyThresholds:
    """벡터 단계의 1위 신뢰도로 갈림길을 정한다. 숫자는 환경변수에서 온다(docs/ai/README.md 4장).

    min_confidence 이상 → 그대로 쓴다(LLM 0회). abstain_below 미만 → 모른다고 한다.
    그 사이 → LLM이 근거를 보고 고른다.
    """

    min_confidence: float
    abstain_below: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.abstain_below <= self.min_confidence <= 1.0:
            raise ValueError("0 ≤ abstain_below ≤ min_confidence ≤ 1이어야 한다")
