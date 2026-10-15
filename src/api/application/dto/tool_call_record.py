from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    """감사 로그의 도구 호출 하나. 인자와 결과는 도구마다 모양이 달라 그대로 받아 둔다.

    `call_id`는 실행 안에서 유일하다 — 같은 도구를 두 번 부른 대화에서 어느 결과인지 가린다
    (docs/ai/tools.md 3.1).
    """

    call_id: str
    tool: str
    args: Mapping[str, object]
    result: Mapping[str, object] | None
