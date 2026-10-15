from __future__ import annotations

from typing import Protocol

from agent.application.dto import RunRecord


class RunRecorder(Protocol):
    """감사 로그를 남기는 곳 — agent는 DB를 모르니 api에 맡긴다(docs/ai/README.md 3장).

    닿지 못하면 `LedgerUnavailable`, api가 거절하면 `LedgerRejected`. 실패를 삼키는 것은
    부르는 쪽(RecordRun)의 일이다 — 어댑터는 실패를 숨기지 않는다.
    """

    async def record(self, run: RunRecord, model: str) -> None:
        """`model`은 그 실행이 쓴 LLM의 이름이다. 같은 실행을 다시 보내도 한 줄이다."""
        ...
