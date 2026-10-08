from __future__ import annotations

import json
from dataclasses import dataclass, field

from agent.domain.tools import CategoryLine

from .loop_outcome import LoopOutcome
from .model_usage import ModelUsage
from .stop_reason import StopReason
from .tool_call import ToolCall
from .tool_result import ToolResult
from .tool_step import ToolStep

FIXES_PER_TOOL = 2  # validation_error를 모델이 고칠 기회(ai/agent-loop.md 7장)


@dataclass
class LoopState:
    """실행 하나의 상태(ai/agent-loop.md 4.1). 루프 안에서만 바뀐다."""

    started: float  # 벽시계의 시작 — 단조 시계의 초
    calls: int = 0  # LLM 호출 수. 스텝 상한이 이것을 센다
    usage: ModelUsage = field(default_factory=ModelUsage)
    steps: list[ToolStep] = field(default_factory=list)
    malformed: bool = False  # 모델 출력의 모양이 한 번 틀렸다
    categories: tuple[CategoryLine, ...] = ()
    _seen: set[tuple[str, str]] = field(default_factory=set)
    _failures: dict[str, int] = field(default_factory=dict)

    def first_time(self, call: ToolCall) -> bool:
        """(도구 이름, 인자)를 쌓는다. 두 번째면 False — 읽기 도구는 다시 불러도 같은 답이다."""
        key = (call.name, json.dumps(dict(call.arguments), sort_keys=True, ensure_ascii=False))
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def failed_too_often(self, call: ToolCall, result: ToolResult) -> bool:
        """같은 도구가 validation_error를 고칠 기회를 다 쓰고도 또 틀렸나."""
        if result.error is None or result.error.code != "validation_error":
            return False
        self._failures[call.name] = self._failures.get(call.name, 0) + 1
        return self._failures[call.name] > FIXES_PER_TOOL

    def end(self, stop: StopReason, text: str = "") -> LoopOutcome:
        return LoopOutcome(stop, text, tuple(self.steps), self.usage, self.calls, self.categories)
