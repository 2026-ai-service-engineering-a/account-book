from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ui.application.values import RunId


@dataclass(frozen=True, slots=True)
class RunLine:
    """감사 로그의 실행 한 줄(ui_docs/pages/runs.md). 값은 api가 낸 그대로다 — 이름으로 옮기는
    것은 화면의 일이다. `tool_count`는 목록에서는 api가, 실행 하나에서는 호출의 수다."""

    id: RunId
    seat: str
    flow: str
    utterance: str
    model: str
    steps: int
    tokens: int
    cost_usd: Decimal
    status: str
    stop_reason: str
    client: str | None  # mcp 자리만
    created_at: datetime
    tool_count: int
