from __future__ import annotations

from dataclasses import dataclass

from agent.domain.tools import ToolSpec

from .turn import Turn


@dataclass(frozen=True, slots=True)
class ToolPrompt:
    """도구를 줄 수 있는 LLM 호출 한 번. `tools`가 그 자리의 능력 범위다(ai/tools.md 6장)."""

    name: str  # 어느 흐름의 호출인가 — 로그와 테이프에서 가린다
    system: str
    turns: tuple[Turn, ...]
    tools: tuple[ToolSpec, ...]
