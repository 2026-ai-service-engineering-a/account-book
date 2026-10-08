from __future__ import annotations

from dataclasses import dataclass

from .model_usage import ModelUsage
from .tool_call import ToolCall


@dataclass(frozen=True, slots=True)
class ModelReply:
    """도구를 줄 수 있는 호출의 답 — 도구 호출들이거나, 도구 없이 쓴 글이다.

    도구 없이 답이 오면 루프는 정상 종료한다(ai/agent-loop.md 4.2).
    """

    text: str
    tool_calls: tuple[ToolCall, ...]
    usage: ModelUsage
