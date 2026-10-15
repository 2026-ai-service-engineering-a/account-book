from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from api.domain.values import RunFlow, RunSeat, RunStatus

from .tool_call_record import ToolCallRecord


@dataclass(frozen=True, slots=True)
class RunRecord:
    """끝난 에이전트 실행 하나와 그 도구 호출들(docs/ai/agent-loop.md 9장).

    발화 원문이 여기에 있다 — 운영 로그가 아니라 감사 테이블에만 남는다(development-rules 6.4).
    """

    id: str
    seat: RunSeat
    flow: RunFlow
    utterance: str
    model: str
    steps: int  # LLM 호출 수. 단발 자리는 아직 세지 않아 0이다
    tokens: int
    cost_usd: Decimal
    status: RunStatus
    stop_reason: str
    tool_calls: tuple[ToolCallRecord, ...] = ()
    created_at: datetime | None = None  # 읽을 때만 — 제안의 수명(24시간)을 잰다
