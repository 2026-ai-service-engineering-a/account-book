from __future__ import annotations

from enum import StrEnum


class StopReason(StrEnum):
    """루프가 왜 멈췄나. 무엇에 걸렸는지를 남겨야 대응이 갈린다(ai/agent-loop.md 8장)."""

    ANSWERED = "answered"  # 도구 없이 답이 왔다 — 정상 종료
    MAX_STEPS = "max_steps"
    MAX_COST = "max_cost"
    WALL_CLOCK = "wall_clock"
    REPEATED = "repeated"  # 같은 (도구, 인자)가 두 번 — 4.3
    TOOL_FAILED = "tool_failed"  # 같은 도구의 인자를 두 번 고쳐도 틀렸다 — 7장
    MALFORMED = "malformed"  # 모델 출력이 두 번 모양을 못 맞췄다
    MODEL_UNAVAILABLE = "model_unavailable"
    LEDGER_UNAVAILABLE = "ledger_unavailable"
