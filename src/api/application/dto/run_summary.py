from __future__ import annotations

from dataclasses import dataclass

from .run_record import RunRecord


@dataclass(frozen=True, slots=True)
class RunSummary:
    """목록의 한 줄 — 실행과 그 도구 호출의 수. 인자와 결과는 싣지 않는다.

    `run.tool_calls`는 비어 있다. 호출은 실행 하나를 읽을 때 가져온다.
    """

    run: RunRecord
    tool_count: int
