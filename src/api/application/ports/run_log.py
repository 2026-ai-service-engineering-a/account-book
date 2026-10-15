from __future__ import annotations

from typing import Protocol

from api.application.dto import RunRecord


class RunLog(Protocol):
    """감사 로그 — `agent_runs`와 `tool_calls`(docs/ai/README.md 2장 원칙 7).

    넣기만 한다. 고치거나 지우는 길은 없다 — 사후에 대조하려고 남기는 기록이다.
    """

    def add(self, run: RunRecord) -> None:
        """실행 하나와 그 도구 호출들을 넣는다. 커밋은 부르는 쪽(멱등 쓰기)이 한다."""
        ...
