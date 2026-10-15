from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    """감사 로그에 남길 도구 호출 하나 — 인자와 결과를 그대로. 운영 로그에는 싣지 않는다."""

    call_id: str
    tool: str
    args: Mapping[str, object]
    result: Mapping[str, object] | None
