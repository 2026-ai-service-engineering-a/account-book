from __future__ import annotations

from dataclasses import dataclass

from agent.domain.tools import CategoryLine

from .model_usage import ModelUsage
from .stop_reason import StopReason
from .tool_step import ToolStep


@dataclass(frozen=True, slots=True)
class LoopOutcome:
    """끝난 실행. 끊긴 실행도 그때까지 모은 스텝으로 답을 낸다 — 조용히 멈추지 않는다."""

    stop: StopReason
    text: str  # 모델이 도구 없이 쓴 답. 정상 종료가 아니면 비어 있다
    steps: tuple[ToolStep, ...]
    usage: ModelUsage
    model_calls: int
    categories: tuple[CategoryLine, ...] = ()  # 표에 카테고리 이름을 쓰려고 들고 간다
