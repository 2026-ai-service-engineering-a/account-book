from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolError:
    """봉투의 실패 칸. `hint`는 우리가 쓴 문장이다 — api의 message를 넘기지 않는다
    (ai/tools.md 5장)."""

    code: str
    retryable: bool  # 모델이 인자를 고쳐 다시 부를 만한가. 재시도 자체는 루프가 정한다
    hint: str
