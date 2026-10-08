from __future__ import annotations

import dataclasses
from collections.abc import Callable, Collection
from datetime import date, datetime, time, timedelta, tzinfo

from agent.application.dto import CategoryQuery, ToolCall, ToolError, ToolMeta, ToolResult
from agent.application.dto import TransactionFilter as Filter
from agent.application.errors import InvalidToolArguments, LedgerRejected, LedgerUnavailable
from agent.application.parsers import ToolInput, parse_tool_arguments
from agent.application.ports import LedgerApi
from agent.domain.tools import (
    CategoryLine,
    CategorySuggestion,
    ComparePeriodsInput,
    CountFrequencyInput,
    DocumentLine,
    EvidenceLine,
    GetBudgetStatusInput,
    SearchDocumentsInput,
    SearchTransactionsInput,
    SuggestCategoryInput,
    SuggestedCategory,
    SummarizeSpendingInput,
    ToolName,
)
from agent.domain.values import Amount, TimeRange

from .retrieve import Retrieve
from .tool_payload import fit, plain

_MAX_CHANGES = 30  # compare_periods의 카테고리 상한(ai/tools.md 4.1)
_MAX_EVIDENCE = 8  # suggest_category의 근거 상한

type _Outcome = tuple[dict[str, object], ToolMeta]


class RunTool:
    """도구 실행기 — 이름과 인자를 받아 기간을 풀고, api를 한 번 부르고, 봉투로 돌려준다.

    실패도 봉투다(ok: false). 예외를 위로 던지지 않는다 — 모델이 읽고 다음 수를 고칠 수
    있어야 한다(ai/tools.md 5장). 재시도하지 않는다. LLM을 부르지 않는다.
    `tools`는 그 자리(모드)에서 쓸 수 있는 도구다. 목록 밖의 이름은 부르지 않는다.
    search_documents는 /retrieve와 같은 찾기(`retrieve`)를 쓴다 — 임베딩은 하되 생성은 없다.
    """

    def __init__(
        self,
        ledger: LedgerApi,
        retrieve: Retrieve,
        tools: Collection[ToolName],
        timer: Callable[[], float],
    ) -> None:
        self._ledger = ledger
        self._retrieve = retrieve
        self._tools = frozenset(tools)
        self._timer = timer  # 초 단위 단조 시계 — elapsed_ms를 잰다

    async def __call__(self, call: ToolCall, today: date, zone: tzinfo) -> ToolResult:
        """`today`는 사용자 타임존의 오늘이다. 기간 이름은 이것으로 푼다."""
        started = self._timer()
        offered = next((t for t in self._tools if t.value == call.name), None)
        if offered is None:
            hint = f"{call.name}은 이 자리에서 쓸 수 있는 도구가 아니다"
            return ToolResult(call.call_id, error=ToolError("validation_error", False, hint))
        try:
            arguments = parse_tool_arguments(offered, call.arguments)
            data, meta = await self._run(arguments, today, zone)
        except InvalidToolArguments as error:
            hint = f"{error.field}: {error.hint}"
            return ToolResult(call.call_id, error=ToolError("validation_error", True, hint))
        except LedgerRejected as error:
            return ToolResult(call.call_id, error=_rejection(error))
        except LedgerUnavailable:
            hint = "api에 닿지 못했다. 한 번만 다시 부를 수 있다"
            return ToolResult(call.call_id, error=ToolError("internal_error", True, hint))
        elapsed = round((self._timer() - started) * 1000)
        return ToolResult(call.call_id, data, dataclasses.replace(meta, elapsed_ms=elapsed))

    async def _run(self, arguments: ToolInput, today: date, zone: tzinfo) -> _Outcome:
        match arguments:
            case SearchTransactionsInput():
                return await self._search(arguments, today, zone)
            case SummarizeSpendingInput() | CountFrequencyInput():
                period = arguments.period.bounds(today, zone)
                where = Filter(
                    period, arguments.category_id, arguments.merchant, arguments.direction
                )
                if isinstance(arguments, CountFrequencyInput):
                    found: object = await self._ledger.frequency(where)
                else:
                    found = await self._ledger.summary(where)
                return _single(found, {"period": period})
            case ComparePeriodsInput():
                return await self._compare(arguments, today, zone)
            case GetBudgetStatusInput():
                period = arguments.period.bounds(today, zone)
                month = period.start.date()  # 달 이름만 받으니 그 달 1일이다
                lines = await self._ledger.budget_status(month, arguments.category_id)
                return _rows({"budgets": plain(lines)}, "budgets", {"period": period})
            case SuggestCategoryInput():
                return await self._suggest(arguments)
            case SearchDocumentsInput():
                return await self._documents(arguments)

    async def _search(
        self, arguments: SearchTransactionsInput, today: date, zone: tzinfo
    ) -> _Outcome:
        period = arguments.period.bounds(today, zone)
        where = Filter(period, arguments.category_id, arguments.merchant, arguments.direction)
        page = await self._ledger.transactions(where, arguments.limit)
        # api는 UTC로 낸다. 모델이 날짜를 잘못 읽지 않게 사용자 타임존으로 옮긴다
        lines = [
            dataclasses.replace(t, occurred_at=t.occurred_at.astimezone(zone))
            for t in page.transactions
        ]
        data: dict[str, object] = {"transactions": plain(lines), "has_more": page.has_more}
        return _rows(data, "transactions", {"period": period}, more=page.has_more)

    async def _compare(self, arguments: ComparePeriodsInput, today: date, zone: tzinfo) -> _Outcome:
        a, b = arguments.a.bounds(today, zone), arguments.b.bounds(today, zone)
        a, aligned = _same_length(a, b, today, zone)
        shifts = await self._ledger.compare(a, b, arguments.category_id)
        data: dict[str, object] = {"changes": plain(shifts[:_MAX_CHANGES])}
        data, meta = _rows(data, "changes", {"a": a, "b": b}, more=len(shifts) > _MAX_CHANGES)
        return data, dataclasses.replace(meta, note=" ".join(filter(None, (aligned, meta.note))))

    async def _suggest(self, arguments: SuggestCategoryInput) -> _Outcome:
        # 벡터 없이 묻는다 — 임베딩도 모델 호출이다. 규칙·이력 단계까지만 간다
        found = await self._ledger.suggest(
            CategoryQuery(arguments.merchant, arguments.memo, arguments.direction)
        )
        suggestion = CategorySuggestion(
            strategy=found.strategy.value,
            candidates=tuple(
                SuggestedCategory(c.category_id, c.confidence) for c in found.candidates
            ),
            evidence=tuple(
                EvidenceLine(e.merchant, e.memo, e.category_id, Amount(e.amount.amount), e.day)
                for e in found.evidence[:_MAX_EVIDENCE]
            ),
            categories=tuple(CategoryLine(c.id, c.name) for c in found.categories),
        )
        data = plain(suggestion)
        assert isinstance(data, dict)
        return _rows(data, "candidates", {})

    async def _documents(self, arguments: SearchDocumentsInput) -> _Outcome:
        found = await self._retrieve(arguments.query)
        lines = [
            DocumentLine(DocumentLine.ref_for(c.id), c.title, c.heading, c.effective_date, c.body)
            for c in found.chunks
        ]
        data: dict[str, object] = {"chunks": plain(lines)}
        trimmed = fit(data, "chunks")
        rows = data["chunks"]
        count = len(rows) if isinstance(rows, list) else 0
        notes = [f"{count}조각까지만 보여줬다." if trimmed else ""]
        notes.append("임베딩을 못 해 낱말로만 찾았다." if found.fell_back else "")
        return data, ToolMeta(count, trimmed, 0, {}, " ".join(filter(None, notes)))


def _single(found: object, periods: dict[str, TimeRange]) -> _Outcome:
    data = plain(found)
    assert isinstance(data, dict)
    return data, ToolMeta(row_count=1, truncated=False, elapsed_ms=0, periods=periods)


def _rows(
    data: dict[str, object], key: str, periods: dict[str, TimeRange], more: bool = False
) -> _Outcome:
    trimmed = fit(data, key)
    rows = data[key]
    count = len(rows) if isinstance(rows, list) else 0
    truncated = more or trimmed
    note = f"{count}줄까지만 보여줬다. 더 있다 — 기간이나 조건을 좁혀라." if truncated else ""
    return data, ToolMeta(count, truncated, 0, periods, note)


def _same_length(a: TimeRange, b: TimeRange, today: date, zone: tzinfo) -> tuple[TimeRange, str]:
    """b가 진행 중(오늘을 품었다)이면 a를 b가 지나온 날 수만큼 자른다.

    10월 8일에 "지난달보다 늘었어?"를 9월 전체와 견주면 늘 줄었다고 나온다.
    """
    midnight = datetime.combine(today, time(0), tzinfo=zone)
    if not b.start <= midnight < b.end:
        return a, ""
    elapsed = midnight + timedelta(days=1) - b.start
    clipped = a.first(elapsed)
    if clipped == a:
        return a, ""
    return clipped, f"b가 진행 중이라 a를 같은 길이({elapsed.days}일)로 잘라 견줬다."


def _rejection(error: LedgerRejected) -> ToolError:
    """api의 거절을 모델이 읽을 실패로(ai/tools.md 5장의 표)."""
    if error.code == "validation_error":
        fields = ", ".join(f"{k}: {v}" for k, v in error.details.items()) or "인자"
        return ToolError("validation_error", True, f"api가 인자를 거절했다 — {fields}")
    if error.code == "not_found":
        return ToolError("not_found", False, "찾는 것이 없다. 다시 찾지 않는다")
    return ToolError(error.code, False, "api가 이 요청을 받지 않는다")
