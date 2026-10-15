from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from api.application.dto import RunRecord
from api.domain.values import RunStatus


class RunLog(Protocol):
    """감사 로그 — `agent_runs`와 `tool_calls`(docs/ai/README.md 2장 원칙 7).

    대부분은 넣기만 한다. 고치는 길은 쓰기 제안 하나뿐이고 좁다 —
    대기(`awaiting_confirmation`)인 실행의 상태·끝난 이유·`confirmed_at`·결과만 바꾼다.
    발화와 인자는 고치지 않는다. 지우는 길은 없다.
    """

    def add(self, run: RunRecord) -> None:
        """실행 하나와 그 도구 호출들을 넣는다. 커밋은 부르는 쪽(멱등 쓰기)이 한다."""
        ...

    def get(self, run_id: str) -> RunRecord | None: ...

    def confirm(self, run_id: str, call_id: str, at: datetime) -> None:
        """대기인 실행의 그 호출에 `confirmed_at`이 비어 있으면 채운다.
        그 밖에는 아무것도 하지 않는다."""
        ...

    def close(
        self,
        run_id: str,
        status: RunStatus,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]],
    ) -> None:
        """대기인 실행을 닫는다. 확인된 호출이 있으면 `aborted`로는 닫지 않는다 — 확인된 제안은
        취소되지 않는다. 그 밖에는 아무것도 하지 않는다. `results`는 call_id → 결과."""
        ...
