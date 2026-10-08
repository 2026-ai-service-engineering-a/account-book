from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoopLimits:
    """루프의 상한(ai/agent-loop.md 8장). 스텝·비용은 환경변수, 벽시계는 흐름이 정한다."""

    max_steps: int  # AGENT_MAX_STEPS — LLM 호출 수
    max_cost_usd: float  # AGENT_MAX_COST_USD
    wall_seconds: float

    def __post_init__(self) -> None:
        if self.max_steps < 1 or self.max_cost_usd <= 0 or self.wall_seconds <= 0:
            raise ValueError("상한은 0보다 커야 한다")
