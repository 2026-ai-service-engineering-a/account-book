from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta

from ui.application.dto import (
    ChatEvent,
    Direction,
    Period,
    Proposal,
    Transaction,
    TransactionDraft,
)
from ui.application.errors import LedgerValidationError
from ui.application.ports import (
    BudgetGateway,
    CatalogGateway,
    CategorySuggester,
    Clock,
    ReportGateway,
    TransactionGateway,
)
from ui.application.values import AccountId, CategoryId, IdempotencyKey, Money, ProposalId, RunId

from .parsed_utterance import ParsedUtterance
from .utterance_parser import UtteranceParser

_FALLBACK = (
    "저는 아직 각본 대역이라 정해진 모양만 알아들어요.\n"
    "'어제 점심 김밥천국 8500원 카드로' 같은 기록이나 "
    "'이번 달 식비 얼마 썼어?' 같은 질문을 해 보세요."
)
_OTHER_PERIOD = (
    "저는 아직 각본 대역이라 기간은 이번 달과 지난달만 읽어요.\n"
    "다른 달은 리포트 화면에서 달을 바꿔 보세요."
)


class ScriptedChatAgent:
    """키 없이 도는 agent 대역. 목 UI와 테스트가 이걸 쓴다.

    진짜 agent처럼 api 포트만 불러서 일한다 — 숫자는 전부 저쪽이 낸다.
    쓰기는 제안 → 확인 → 실행 세 박자를 그대로 지킨다(README 5장).
    """

    def __init__(
        self,
        transactions: TransactionGateway,
        reports: ReportGateway,
        budgets: BudgetGateway,
        catalog: CatalogGateway,
        suggester: CategorySuggester,
        clock: Clock,
        token_delay: float = 0.03,
    ) -> None:
        self._transactions = transactions
        self._reports = reports
        self._budgets = budgets
        self._catalog = catalog
        self._suggester = suggester
        self._clock = clock
        self._delay = token_delay
        self._parser = UtteranceParser()
        self._pending: dict[ProposalId, tuple[RunId, TransactionDraft]] = {}

    async def run(self, utterance: str) -> AsyncIterator[ChatEvent]:
        parsed = self._parser.parse(utterance)
        if parsed.is_question:
            async for event in self._answer(utterance, parsed):
                yield event
        elif parsed.amount:
            async for event in self._propose(parsed):
                yield event
        else:
            async for event in self._say(_FALLBACK):
                yield event
        yield ChatEvent("done")

    async def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        pending = self._pending.pop(proposal_id, None)
        if pending is None:
            yield ChatEvent(
                "error", "그 제안을 찾지 못했어요. 이미 처리했을 수 있어요.", code="not_found"
            )
        elif not accepted:
            async for event in self._say("취소했어요. 기록하지 않았습니다."):
                yield event
        else:
            async for event in self._record(*pending):
                yield event
        yield ChatEvent("done")

    async def _propose(self, parsed: ParsedUtterance) -> AsyncIterator[ChatEvent]:
        if parsed.amount is None:
            return
        yield ChatEvent("tool", "suggest_category")
        suggestion = await self._suggester.suggest(parsed.merchant, "", parsed.direction)
        fallback = CategoryId("etc" if parsed.direction == Direction.EXPENSE else "other_income")
        category_id = suggestion.category_id or fallback
        draft = TransactionDraft(
            direction=parsed.direction,
            amount=parsed.amount,
            occurred_at=self._when(parsed),
            category_id=category_id,
            account_id=parsed.account_id or AccountId("card"),
            merchant=parsed.merchant,
        )
        yield ChatEvent("tool", "create_transaction")
        proposal_id = ProposalId(uuid.uuid4().hex)
        self._pending[proposal_id] = (RunId(uuid.uuid4().hex), draft)
        yield ChatEvent("proposal", proposal=await self._proposal(proposal_id, draft))

    async def _record(self, run_id: RunId, draft: TransactionDraft) -> AsyncIterator[ChatEvent]:
        yield ChatEvent("tool", "create_transaction")
        try:
            # 재시도해도 같은 키가 나온다 — {run_id}:{호출 순번}
            key = IdempotencyKey(f"{run_id}:1")
            saved = await self._transactions.create(draft, key, run_id=run_id)
        except LedgerValidationError as error:
            yield ChatEvent("error", " ".join(error.details.values()), code="validation_error")
            return
        lines = ["기록했어요."]
        if saved.direction == Direction.EXPENSE:
            yield ChatEvent("tool", "get_budget_status")
            lines += await self._budget_lines(saved)
        async for event in self._say("\n".join(lines)):
            yield event

    async def _budget_lines(self, saved: Transaction) -> list[str]:
        period = Period.of(saved.occurred_at.date())
        status = await self._budgets.status(saved.category_id, period)
        if status.limit is None:
            return []
        name = status.category.name
        spent, limit = f"{status.spent:,}원", f"{status.limit:,}원"
        lines = [f"{period.month}월 {name} {spent} / 예산 {limit} ({status.percent}%)."]
        if status.over_on and status.projected is not None:
            lines.append(
                f"지금 페이스면 {status.over_on.month}월 {status.over_on.day}일에 예산을 넘고, "
                f"말일에 {status.projected:,}원이 됩니다."
            )
        return lines

    async def _answer(self, utterance: str, parsed: ParsedUtterance) -> AsyncIterator[ChatEvent]:
        if parsed.other_period:
            async for event in self._say(_OTHER_PERIOD):
                yield event
            return
        today = self._clock.now().date()
        period = Period.of(today)
        if parsed.previous_month:
            period = period.previous()
        yield ChatEvent("tool", "summarize_spending")
        report = await self._reports.monthly(period)
        categories = await self._catalog.categories(Direction.EXPENSE)
        named = next((c for c in categories if c.name in utterance), None)
        # 해석한 기간을 늘 밝힌다 — 경계를 다르게 생각한 사람이 바로 알아챈다(chat-analytics 5장)
        through = today.day if period.contains(today) else period.days
        name = "지난달" if parsed.previous_month else "이번 달"
        when = f"{name}({period.month}/1~{period.month}/{through})"
        if named is None:
            text = (
                f"{when} 지출은 {report.totals.expense:,}원, "
                f"수입은 {report.totals.income:,}원이에요."
            )
        else:
            change = next((c for c in report.by_category if c.category.id == named.id), None)
            spent = change.this_month if change else Money(0)
            text = f"{when} {named.name}에 {spent:,}원 썼어요."
            if change and change.delta:
                more = "많습니다" if change.delta.amount > 0 else "적습니다"
                before = "그 전 달" if parsed.previous_month else "지난달"
                text += f" {before}보다 {abs(change.delta):,}원 {more}."
        async for event in self._say(text):
            yield event

    async def _say(self, text: str) -> AsyncIterator[ChatEvent]:
        for start in range(0, len(text), 6):
            yield ChatEvent("token", text[start : start + 6])
            await asyncio.sleep(self._delay)
        yield ChatEvent("message", text)

    def _when(self, parsed: ParsedUtterance) -> datetime:
        now = self._clock.now()
        day = now + timedelta(days=parsed.day_offset)
        if parsed.at is not None:
            return datetime.combine(day.date(), parsed.at, tzinfo=now.tzinfo)
        return day if parsed.day_offset == 0 else day.replace(hour=12, minute=0, second=0)

    async def _proposal(self, proposal_id: ProposalId, draft: TransactionDraft) -> Proposal:
        categories = {c.id: c.name for c in await self._catalog.categories()}
        accounts = {a.id: a.name for a in await self._catalog.accounts()}
        return Proposal(
            id=proposal_id,
            occurred_on=draft.occurred_at.date(),
            category_name=categories.get(draft.category_id, draft.category_id),
            direction=draft.direction,
            amount=draft.amount,
            account_name=accounts.get(draft.account_id, draft.account_id),
            merchant=draft.merchant,
        )
