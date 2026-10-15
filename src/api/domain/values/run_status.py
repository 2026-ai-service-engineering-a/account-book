from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    """실행의 상태. 대부분은 끝날 때 한 번 남긴다 — 그때는 `done`이나 `failed`다.

    쓰기 제안만 사람을 기다린다(docs/ai/agent-loop.md 6장): `awaiting_confirmation`으로 넣고,
    확인되면 `done`, 취소·만료면 `aborted`로 닫는다. 왜 그렇게 끝났는지는 `stop_reason`이 말한다.
    """

    DONE = "done"
    FAILED = "failed"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    ABORTED = "aborted"
