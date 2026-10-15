from __future__ import annotations

from sqlalchemy.orm import Session

from api.application.dto import RunRecord

from .rows import AgentRunRow, ToolCallRow


class SqlRunLog:
    """감사 로그를 Postgres에. 실행과 도구 호출이 같은 세션 — 한 트랜잭션에 들어간다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, run: RunRecord) -> None:
        self._session.add(
            AgentRunRow(
                id=run.id,
                seat=run.seat.value,
                flow=run.flow.value,
                utterance=run.utterance,
                model=run.model,
                steps=run.steps,
                tokens=run.tokens,
                cost_usd=run.cost_usd,
                status=run.status.value,
                stop_reason=run.stop_reason,
            )
        )
        # 실행 줄이 먼저 있어야 외래 키가 맞는다
        self._session.flush()
        self._session.add_all(
            ToolCallRow(
                run_id=run.id,
                call_id=c.call_id,
                tool=c.tool,
                args=dict(c.args),
                result=dict(c.result) if c.result is not None else None,
            )
            for c in run.tool_calls
        )
