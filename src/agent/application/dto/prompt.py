from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Prompt:
    """구조화 출력을 받는 LLM 호출 한 번. 답은 `schema` 모양의 JSON 객체 하나다."""

    name: str  # 스키마 이름. 제공자가 구조화 출력에 붙이는 이름이다
    system: str
    user: str
    schema: Mapping[str, object]
