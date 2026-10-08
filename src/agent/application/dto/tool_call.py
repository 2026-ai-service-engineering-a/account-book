from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolCall:
    """모델이 고른 도구 호출 하나. 이름과 인자는 아직 검사하지 않은 바깥 값이다.

    `call_id`는 루프가 정한다 — 감사 로그의 키이고, 같은 도구를 두 번 부른 대화에서 어느
    결과인지 가린다(ai/tools.md 3.1).
    """

    call_id: str
    name: str
    arguments: Mapping[str, object]
