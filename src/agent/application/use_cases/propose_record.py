from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime

from agent.application.dto import RecordReply
from agent.application.errors import LedgerUnavailable
from agent.application.ports import LedgerApi, RunRecorder
from agent.domain.tools import CreateTransactionInput
from agent.domain.values import CategoryChoice

from .read_capture import ReadCapture
from .record_entry import card_of, entry_of, proposal_run
from .record_run import RecordRun
from .run_records import capture_run

_log = logging.getLogger(__name__)

NOT_SAVED = "제안을 남기지 못해 기록하지 않았어요. 잠시 뒤 다시 보내 주세요."


def _new_id() -> str:
    return str(uuid.uuid4())


class ProposeRecord:
    """채팅의 기록 — 읽기 → 분류 → 제안. 순서는 코드가 정한다(docs/ai/chat-capture.md 결정 1).

    읽기와 분류는 폼의 한 줄로 채우기(`ReadCapture`)와 같다. 쓰지 않는다 — 제안을 감사 테이블에
    `awaiting_confirmation`으로 남기고 확인 카드를 낼 뿐이다. **저장이 실패하면 카드를 내지
    않는다** — 남지 않은 제안은 확인할 수 없다. 모델에 닿지 못하면 `ModelUnavailable`이 올라간다.
    """

    def __init__(
        self,
        read: ReadCapture,
        ledger: LedgerApi,
        recorder: RunRecorder,
        record: RecordRun,
        model: str,
        new_id: Callable[[], str] = _new_id,
    ) -> None:
        self._read = read
        self._ledger = ledger
        self._recorder = recorder
        self._record = record
        self._model = model
        self._new_id = new_id

    async def __call__(self, text: str, now: datetime) -> RecordReply:
        """`now`는 사용자 타임존의 기준 시각 — 말하지 않은 날짜는 지금이다."""
        reading = await self._read(text, now)
        if reading.refusal:
            await self._record(capture_run(self._new_id(), text, reading))
            return RecordReply(text=reading.refusal)
        entry, unsure = entry_of(reading, now)
        return await self.propose(text, entry, unsure, reading.category)

    async def propose(
        self,
        text: str,
        entry: CreateTransactionInput,
        unsure: tuple[str, ...] = (),
        choice: CategoryChoice | None = None,
    ) -> RecordReply:
        """칸이 정해진 제안을 남기고 카드를 낸다. 만료된 제안을 다시 낼 때도 이 길이다."""
        run_id = self._new_id()
        try:
            await self._recorder.record(proposal_run(run_id, text, entry, choice), self._model)
        except LedgerUnavailable as error:
            _log.warning("proposal not saved run_id=%s code=%s", run_id, type(error).__name__)
            return RecordReply(text=NOT_SAVED, code="proposal_not_saved")
        return RecordReply(card=card_of(run_id, entry, await self._names(), unsure))

    async def _names(self) -> dict[str, str]:
        try:
            return {c.id: c.name for c in await self._ledger.categories()}
        except LedgerUnavailable:
            return {}  # 이름을 못 읽으면 id를 보인다 — 제안은 이미 남았다
