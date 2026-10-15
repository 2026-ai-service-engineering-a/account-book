from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    """실행이 어떻게 끝났나. 끝날 때 한 번만 남기므로 진행 중 상태는 아직 없다.

    모른다고 답한 것·부분 결과는 `done`이다 — 답이 나갔다. `failed`는 503으로 끝난 실행이다.
    왜 그렇게 끝났는지는 `stop_reason`이 말한다.
    """

    DONE = "done"
    FAILED = "failed"
