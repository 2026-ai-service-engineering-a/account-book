from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from agent.application.dto import RecordReply, StoredProposal
from agent.application.errors import InvalidToolArguments, LedgerRejected, LedgerUnavailable
from agent.application.parsers import parse_tool_arguments
from agent.application.ports import LedgerApi, ProposalBook
from agent.domain.tools import CreateTransactionInput, ToolName, TransactionLine

from .propose_record import ProposeRecord

_log = logging.getLogger(__name__)

LIFETIME = timedelta(hours=24)  # 멱등 키 보존 기간과 같다(agent-loop 6장, api-contract 3장)
RECORDED = "기록했어요."
ALREADY = "이미 기록했어요."
IN_PROGRESS = "이미 기록하고 있어요."
CLOSED = "취소했거나 시간이 지난 제안이에요. 다시 보내 주세요."
CANCELLED = "취소했어요. 기록하지 않았습니다."
EXPIRED = "시간이 지나 다시 확인할게요."
MISSING = "그 제안을 찾지 못했어요."
UNREACHABLE = "지금은 기록하지 못했어요. 다시 눌러 주세요."


class DecideRecord:
    """확인 카드의 답(docs/ai/chat-capture.md 5장).
    제안은 감사 테이블에 있다 — 재시작해도 이어 간다.

    확인은 제안 때 정한 키(`{run_id}:{seq}`)와 `X-Confirmed-By`로 api를 부른다. 한 건을 지키는
    것은 상태가 아니라 멱등 키다 — 두 번 누름과 재시작이 같은 길이다.
    """

    def __init__(
        self,
        book: ProposalBook,
        ledger: LedgerApi,
        propose: ProposeRecord,
        clock: Callable[[], datetime],
    ) -> None:
        self._book = book
        self._ledger = ledger
        self._propose = propose
        self._clock = clock  # aware — 제안의 나이를 잰다

    async def confirm(self, proposal_id: str) -> RecordReply:
        try:
            found = await self._book.get(proposal_id)
            if found is None:
                return RecordReply(text=MISSING, code="not_found")
            if not found.waiting:
                return RecordReply(text=ALREADY if found.status == "done" else CLOSED)
            if found.confirmed_at is None and self._clock() - found.created_at >= LIFETIME:
                return await self._renew(found)
            if found.confirmed_at is None:
                found = await self._book.confirm(proposal_id, found.call_id)
                if not found.waiting:  # 그 사이 취소됐다
                    return RecordReply(text=CLOSED)
            return await self._write(found)
        except LedgerUnavailable as error:
            # 상태는 대기 그대로다 — 다음 누름이 같은 키로 이어 간다
            _log.warning("record confirm failed run_id=%s code=%s", proposal_id, _code(error))
            return RecordReply(text=UNREACHABLE, code="ledger_unavailable")

    async def cancel(self, proposal_id: str) -> RecordReply:
        try:
            found = await self._book.get(proposal_id)
            if found is None:
                return RecordReply(text=MISSING, code="not_found")
            if not found.waiting:
                return RecordReply(text=ALREADY if found.status == "done" else CLOSED)
            if found.confirmed_at is not None:
                return RecordReply(text=IN_PROGRESS)
            closed = await self._book.close(proposal_id, "aborted", "cancelled")
        except LedgerUnavailable as error:
            _log.warning("record cancel failed run_id=%s code=%s", proposal_id, _code(error))
            return RecordReply(text=UNREACHABLE, code="ledger_unavailable")
        # 확인된 제안은 취소되지 않는다 — 그 사이 확인이 이겼으면 그대로 둔다
        return RecordReply(text=CANCELLED if closed.status == "aborted" else IN_PROGRESS)

    async def _write(self, found: StoredProposal) -> RecordReply:
        entry = _entry(found)
        try:
            line = await self._ledger.create_transaction(entry, found.idempotency_key, found.run_id)
        except LedgerRejected as error:
            if error.code == "request_in_progress":
                return RecordReply(text=IN_PROGRESS, wrote=True)
            await self._book.close(found.run_id, "failed", "rejected")
            reason = " ".join(error.details.values()) or "값을 받지 않았어요."
            text = f"이 값으로는 기록할 수 없어요: {reason} 폼으로 넣어 주세요."
            return RecordReply(text=text, code=error.code, wrote=True)
        result = {"transaction_id": line.id}
        try:
            await self._book.close(found.run_id, "done", "confirmed", {found.call_id: result})
        except LedgerUnavailable as error:
            # 거래는 들어갔다. 줄은 대기로 남고 다음 확인이 같은 키로 저장된 응답을 받아 닫는다
            _log.warning("record close failed run_id=%s code=%s", found.run_id, _code(error))
        return RecordReply(text=await self._after(entry, line), wrote=True)

    async def _renew(self, found: StoredProposal) -> RecordReply:
        """만료된 제안 — 옛 키는 지워졌을 수 있어 쓰지 않는다. 같은 칸으로 새 제안을 낸다."""
        await self._book.close(found.run_id, "aborted", "expired")
        renewed = await self._propose.propose(found.utterance, _entry(found))
        if renewed.card is None:
            return renewed
        return RecordReply(text=EXPIRED, card=renewed.card)

    async def _after(self, entry: CreateTransactionInput, line: TransactionLine) -> str:
        """기록 뒤 예산 한두 줄 — 대역(ScriptedChatAgent)과 같은 모양이다.
        숫자는 api가 내고 문장은 코드가 쓴다. 넘을 페이스면 언제 넘고 말일에 얼마가 되는지
        한 줄 더. 못 읽으면 빼고 말한다."""
        if line.direction.value != "expense":
            return RECORDED
        month = entry.occurred_at.date().replace(day=1)
        try:
            statuses = await self._ledger.budget_status(month, entry.category_id)
        except LedgerUnavailable:
            return RECORDED
        found = next((b for b in statuses if b.limit is not None), None)
        if found is None or found.limit is None:
            return RECORDED
        budget = (
            f"{month.month}월 {found.name} {found.spent.amount:,}원 / 예산 {found.limit.amount:,}원"
        )
        lines = [RECORDED, f"{budget} ({found.percent}%)."]
        if found.over_on is not None and found.projected is not None:
            when = f"{found.over_on.month}월 {found.over_on.day}일"
            lines.append(
                f"지금 페이스면 {when}에 예산을 넘고, 말일에 {found.projected.amount:,}원이 됩니다."
            )
        return "\n".join(lines)


def _entry(found: StoredProposal) -> CreateTransactionInput:
    try:
        parsed = parse_tool_arguments(ToolName.CREATE_TRANSACTION, found.args)
    except InvalidToolArguments as error:
        raise LedgerUnavailable("저장된 제안의 칸이 틀렸다") from error
    assert isinstance(parsed, CreateTransactionInput)
    return parsed


def _code(error: LedgerUnavailable) -> str:
    return error.code if isinstance(error, LedgerRejected) else "unavailable"
