from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .tool_name import ToolName


@dataclass(frozen=True, slots=True)
class ToolContract:
    """외부에 보이는 도구 하나 — 이름, 설명, 입력 JSON Schema.

    agent의 mcp 모드 스냅샷(src/shared/mcp_tools.json)의 한 줄이다. 여기서 고치지 않는다 —
    설명과 스키마는 agent의 카탈로그가 정하고, 스냅샷 테스트가 파일로 써 낸다.
    """

    name: ToolName
    description: str
    input_schema: Mapping[str, object]
