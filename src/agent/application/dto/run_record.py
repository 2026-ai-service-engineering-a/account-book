from __future__ import annotations

from dataclasses import dataclass

from .run_seat import RunSeat
from .tool_call_record import ToolCallRecord


@dataclass(frozen=True, slots=True)
class RunRecord:
    """끝난 실행 하나(ai/agent-loop.md 9장). 발화 원문이 들어 있다 — 감사 테이블로만 간다.

    `failed`는 503으로 끝난 실행이다. 모른다는 답이나 부분 결과는 답이 나갔으니 실패가 아니다.
    단발 자리는 구조화 출력 호출이 사용량을 내지 않아 `steps`·`tokens`·`cost_usd`가 0이다.
    """

    run_id: str
    seat: RunSeat
    utterance: str
    stop_reason: str
    failed: bool = False
    awaiting: bool = False  # 쓰기 제안 — 사람의 확인을 기다린다(감사 줄이 곧 제안이다)
    steps: int = 0  # LLM 호출 수
    tokens: int = 0
    cost_usd: float = 0.0
    tool_calls: tuple[ToolCallRecord, ...] = ()
