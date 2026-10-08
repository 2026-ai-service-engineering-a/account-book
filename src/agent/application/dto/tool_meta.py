from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from agent.domain.values import TimeRange


@dataclass(frozen=True, slots=True)
class ToolMeta:
    """봉투의 meta. 잘렸는지와 해석한 기간을 모델에게 알린다.

    `periods`는 인자 이름 → 실제로 조회한 경계다. 답에 기간을 밝히는 근거가 된다
    (ai/chat-analytics.md 5장).
    """

    row_count: int  # 목록이면 줄 수, 아니면 1
    truncated: bool
    elapsed_ms: int
    periods: Mapping[str, TimeRange] = field(default_factory=dict)
    note: str = ""  # 잘렸거나 기간을 맞췄으면 그 사실을 문장으로 — 조용히 자르지 않는다
