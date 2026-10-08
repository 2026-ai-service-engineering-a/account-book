from __future__ import annotations

from dataclasses import dataclass

from .loop_outcome import LoopOutcome


@dataclass(frozen=True, slots=True)
class LoopEvent:
    """루프가 흘려보내는 것 — 지금 부르는 도구의 이름이나, 끝난 실행.

    도구 인자는 싣지 않는다. 화면에 필요한 건 "무엇을 하는 중"이다(ui_docs/pages/chat.md 4.1).
    모델의 중간 생각도 싣지 않는다(ai/agent-loop.md 4.1).
    """

    tool: str = ""
    outcome: LoopOutcome | None = None

    def __post_init__(self) -> None:
        if bool(self.tool) == (self.outcome is not None):
            raise ValueError("도구 이름과 끝난 실행 중 하나만 싣는다")
