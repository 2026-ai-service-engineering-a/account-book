from __future__ import annotations

from enum import StrEnum


class RunFlow(StrEnum):
    """실행이 밟은 흐름(docs/ai/agent-loop.md 2장). 흐름마다 헤매는 모양이 달라 따로 본다."""

    SINGLE = "single"  # 단발 — 코드가 순서를 정하고 LLM은 한 자리에서 판단
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"
    DIRECT = "direct"  # LLM 없이 도구 하나 — 판단은 바깥 클라이언트의 모델이 했다(mcp)
