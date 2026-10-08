from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .tool_name import ToolName


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """모델에게 보여주는 도구 하나 — 이름, 설명 두 줄, 입력 JSON Schema(ai/tools.md 2장).

    설명의 둘째 줄이 첫째 줄보다 중요하다. "언제 쓰지 않는가"가 없으면 모델은 아는 도구로
    모든 걸 해결하려 한다.
    """

    name: ToolName
    does: str  # 무엇을 하나
    avoid: str  # 언제 이 도구를 쓰지 않는가
    input_schema: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.does.strip() or not self.avoid.strip():
            raise ValueError("설명은 두 줄 다 있어야 한다")
        if "\n" in self.does or "\n" in self.avoid:
            raise ValueError("설명은 한 줄씩이다")

    @property
    def description(self) -> str:
        return f"{self.does}\n{self.avoid}"
