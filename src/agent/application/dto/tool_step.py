from __future__ import annotations

from dataclasses import dataclass

from .tool_call import ToolCall
from .tool_result import ToolResult


@dataclass(frozen=True, slots=True)
class ToolStep:
    """루프의 한 스텝 — 실제로 실행한 호출과 그 봉투. 관찰은 요약하지 않고 그대로 둔다
    (ai/agent-loop.md 4.1)."""

    call: ToolCall
    result: ToolResult
