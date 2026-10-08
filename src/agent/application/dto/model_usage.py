from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """호출 한 번이 쓴 토큰과 돈. 루프가 스텝마다 더해 예산과 견준다(ai/agent-loop.md 8장)."""

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0  # 제공자가 값을 모르는 모델이면 0 — 그때는 스텝 상한만 남는다

    def __add__(self, other: ModelUsage) -> ModelUsage:
        return ModelUsage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cost_usd + other.cost_usd,
        )
