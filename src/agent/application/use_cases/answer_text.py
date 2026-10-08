"""끝난 실행을 화면에 낼 글로 — 해석 한 줄과 숫자 표(docs/ai/chat-analytics.md 7·8장).

표는 템플릿이 도구 결과로 그린다. 숫자를 모델에게 옮겨 적게 하지 않는다. 모델의 한 줄은
숫자 검증(7.2)을 통과할 때만 붙는다. 해석한 기간은 표의 머리에 늘 날짜로 밝힌다(5장).
조문 조각을 인용했으면 인용 검증(document-rag.md 5.3)을 거쳐 출처를 붙인다.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, timedelta

from agent.application.dto import CitationVerdict, LoopOutcome, StopReason, ToolStep
from agent.application.errors import InvalidToolArguments
from agent.application.parsers import parse_tool_arguments
from agent.domain.tools import CategoryLine, ToolName
from agent.domain.values import PeriodName, PeriodSpec, TimeRange

from . import document_sources as docs
from .citation_check import check_citations
from .number_check import numbers_from_tools, unsupported

UNAVAILABLE = "지금은 답할 수 없어요. 거래 목록에서 직접 볼 수 있어요."
PARTIAL = "여기까지 해봤어요."
UNVERIFIED = "기록으로 확인할 수 있는 답을 찾지 못했어요."
UNCITED = "조문으로 확인할 수 있는 답을 만들지 못했어요."
_ROWS = 5  # 표에 펼치는 줄 수. 나머지는 "외 n개"

_NAMES = {
    PeriodName.TODAY: "오늘",
    PeriodName.YESTERDAY: "어제",
    PeriodName.THIS_WEEK: "이번 주",
    PeriodName.LAST_WEEK: "저번 주",
    PeriodName.THIS_MONTH: "이번 달",
    PeriodName.LAST_MONTH: "지난달",
    PeriodName.THIS_YEAR: "올해",
}


def answer_text(outcome: LoopOutcome, today: date) -> str:
    if outcome.stop in (StopReason.MODEL_UNAVAILABLE, StopReason.LEDGER_UNAVAILABLE):
        return UNAVAILABLE
    tables = [t for t in (_table(s, outcome.categories, today) for s in outcome.steps) if t]
    documents = docs.documents_in(outcome.steps)
    if outcome.stop is not StopReason.ANSWERED:
        return "\n\n".join(p for p in (PARTIAL, *tables, docs.found_lines(documents)) if p)
    sentence = outcome.text.strip()
    if sentence and not verified(sentence, outcome.steps, today):
        sentence = ""  # 지어낸 숫자나 인용이 섞였다 — 문장을 버리고 표만 낸다
    refs = docs.refs_in(sentence)
    found = docs.source_lines(refs, documents) if refs else docs.found_lines(documents)
    if not sentence and found and not tables:
        sentence = UNCITED
    parts = [p for p in (docs.numbered(sentence, refs), *tables, found) if p]
    return "\n\n".join(parts) or UNVERIFIED


def verified(sentence: str, steps: Sequence[ToolStep], today: date) -> bool:
    """숫자는 도구의 것이거나 인용한 조각의 것. 조각을 인용하지 않았으면 도구의 숫자만.

    평가(make eval-chat)의 숫자 일치율도 이것으로 잰다 — 화면이 거르는 것과 같게.
    """
    allowed = numbers_from_tools(steps, today)
    refs = docs.refs_in(sentence)
    plain = docs.without_refs(sentence)
    verdict = check_citations(plain, refs, docs.sources(docs.documents_in(steps)), allowed)
    if verdict is CitationVerdict.MISSING:
        return not unsupported(plain, allowed)
    return verdict is CitationVerdict.OK


def _table(step: ToolStep, categories: tuple[CategoryLine, ...], today: date) -> str:
    data, meta = step.result.data, step.result.meta
    if data is None or meta is None:
        return ""
    try:
        arguments = parse_tool_arguments(ToolName(step.call.name), step.call.arguments)
    except (InvalidToolArguments, ValueError):
        return ""
    target = _target(step.call.arguments, categories)
    periods = meta.periods
    match step.call.name:
        case "count_frequency":
            head = _head(arguments, periods.get("period"), today, target)
            if not _int(data, "count"):
                return f"{head}: 기록이 없어요"
            gap = data.get("avg_gap_days")
            parts = [f"{_int(data, 'count')}번", f"{_int(data, 'day_count')}일"]
            if isinstance(gap, int | float):
                parts.append(f"평균 {gap:g}일 간격")
            parts.append(f"회당 {_won(data.get('avg_amount'))}")
            return f"{head}\n" + " · ".join(parts)
        case "summarize_spending":
            head = _head(arguments, periods.get("period"), today, target)
            line = f"지출 {_won(data.get('expense'))}"
            if _amount(data.get("income")):
                line += f" · 수입 {_won(data.get('income'))}"
            return f"{head}\n{line}"
        case "compare_periods":
            a, b = getattr(arguments, "a", None), getattr(arguments, "b", None)
            head = f"{_label(a, periods.get('a'), today)} → "
            head += _label(b, periods.get("b"), today)
            return _with_rows(head, _rows(data, "changes", _change), "견줄 지출이 없어요")
        case "get_budget_status":
            month = _label(getattr(arguments, "period", None), periods.get("period"), today)
            budgets = _rows(data, "budgets", _budget)
            return _with_rows(f"{month} 예산", budgets, "정한 예산이 없어요")
        case "search_transactions":
            head = _head(arguments, periods.get("period"), today, target)
            return _with_rows(head, _rows(data, "transactions", _transaction), "기록이 없어요")
        case _:
            return ""


def _head(arguments: object, span: TimeRange | None, today: date, target: str) -> str:
    label = _label(getattr(arguments, "period", None), span, today)
    return f"{label} · {target}" if target else label


def _label(spec: object, span: TimeRange | None, today: date) -> str:
    """ "저번 주(9/28~10/4)". 진행 중인 기간의 끝은 오늘까지만 적는다."""
    if not isinstance(spec, PeriodSpec) or span is None:
        return "기간"
    first = span.start.date()
    last = min(span.end.date() - timedelta(days=1), today)
    if spec.name is PeriodName.LAST_N_DAYS:
        name = f"최근 {spec.days}일"
    elif spec.name is PeriodName.MONTH:
        name = f"{first.month}월"
    else:
        name = _NAMES.get(spec.name, "")
    dates = f"{first.month}/{first.day}"
    if last != first:
        dates += f"~{last.month}/{last.day}"
    return f"{name}({dates})" if name else dates


def _target(arguments: Mapping[str, object], categories: tuple[CategoryLine, ...]) -> str:
    category, merchant = arguments.get("category_id"), arguments.get("merchant")
    if isinstance(category, str) and category:
        return next((c.name for c in categories if c.id == category), category)
    return f"'{merchant.strip()}'" if isinstance(merchant, str) and merchant.strip() else ""


def _with_rows(head: str, lines: list[str], empty: str) -> str:
    if not lines:
        return f"{head}: {empty}"
    shown = lines[:_ROWS]
    if len(lines) > _ROWS:
        shown.append(f"외 {len(lines) - _ROWS}개")
    return "\n".join([head, *shown])


def _rows(
    data: Mapping[str, object], key: str, render: Callable[[Mapping[str, object]], str]
) -> list[str]:
    rows = data.get(key)
    if not isinstance(rows, list):
        return []
    return [line for line in (render(r) for r in rows if isinstance(r, Mapping)) if line]


def _change(row: Mapping[str, object]) -> str:
    delta = _amount(row.get("delta"))
    sign = "+" if delta > 0 else "-" if delta < 0 else "±"
    percent = row.get("percent")
    rate = f", {percent}%" if isinstance(percent, int) else ""
    moved = f"{_won(row.get('a'))} → {_won(row.get('b'))}"
    return f"{row.get('name')} {moved} ({sign}{abs(delta):,}원{rate})"


def _budget(row: Mapping[str, object]) -> str:
    if row.get("limit") is None:
        return ""
    percent = row.get("percent")
    rate = f" ({percent}%)" if isinstance(percent, int) else ""
    return f"{row.get('name')} {_won(row.get('spent'))} / {_won(row.get('limit'))}{rate}"


def _transaction(row: Mapping[str, object]) -> str:
    try:
        at = datetime.fromisoformat(str(row.get("occurred_at")))
    except ValueError:
        return ""
    return f"{at.month}/{at.day} {row.get('merchant') or '-'} {_won(row.get('amount'))}"


def _int(data: Mapping[str, object], key: str) -> int:
    value = data.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _amount(value: object) -> int:
    if isinstance(value, Mapping):
        amount = value.get("amount")
        if isinstance(amount, int) and not isinstance(amount, bool):
            return amount
    return 0


def _won(value: object) -> str:
    return f"{_amount(value):,}원"
