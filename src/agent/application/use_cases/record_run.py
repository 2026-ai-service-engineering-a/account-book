from __future__ import annotations

import logging

from agent.application.dto import RunRecord
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.application.ports import RunRecorder

_log = logging.getLogger(__name__)


class RecordRun:
    """끝난 실행을 감사 로그에 남긴다. **기록이 실패해도 답은 나간다**(docs/ai/README.md 원칙 8).

    실패는 여기서 삼키고 운영 로그에 `run_id`와 코드만 남긴다. 예외 메시지는 남기지 않는다 —
    거절 사유(details)에 보낸 값이 섞여 돌아올 수 있다(development-rules 6.4).
    """

    def __init__(self, recorder: RunRecorder, model: str) -> None:
        self._recorder = recorder
        self._model = model

    async def __call__(self, run: RunRecord) -> None:
        try:
            await self._recorder.record(run, self._model)
            return
        except LedgerRejected as error:
            code = error.code
        except LedgerUnavailable:
            code = "unavailable"
        # 감사 기록은 답의 부수 효과다. 어댑터의 버그라도 이미 만든 답을 막지 않게 전부 삼킨다
        except Exception as error:
            code = type(error).__name__
        _log.warning("run record failed run_id=%s code=%s", run.run_id, code)
