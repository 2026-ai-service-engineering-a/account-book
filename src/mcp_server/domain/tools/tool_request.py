from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mcp_server.domain.values import Direction, PeriodSpec

from .tool_name import ToolName


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """검증을 지난 호출 하나. 기간은 이름 그대로이고 경계는 실행할 때 푼다.

    `periods`는 인자 이름 → 기간이다. compare_periods만 a·b 둘이고 나머지는 period 하나다.
    """

    name: ToolName
    periods: Mapping[str, PeriodSpec]
    category_id: str = ""
    merchant: str = ""
    direction: Direction | None = None
