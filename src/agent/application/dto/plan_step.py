from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanStep:
    """계획의 한 단계(ai/agent-loop.md 5.1). 아직 검사하지 않은 모델의 출력이다.

    `why`는 모델이 쓰고 사람이 읽는다 — 감사 로그에 남고 실행에는 쓰이지 않는다.
    `arguments`가 None이면 인자가 JSON 객체가 아니었다 — 그 단계는 버려진다.
    """

    tool: str
    arguments: Mapping[str, object] | None
    why: str
