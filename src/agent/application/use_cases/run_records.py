"""자리마다 끝난 실행을 감사 기록 하나로 옮긴다(ai/agent-loop.md 9장).

도구 호출의 인자와 결과는 그대로 싣는다 — 감사 테이블은 금액·가맹점을 남기는 곳이다
(development-rules 6.4). 운영 로그로 가는 길은 여기에 없다.
"""

from __future__ import annotations

from agent.application.dto import (
    DocumentAnswer,
    LoopOutcome,
    RunRecord,
    RunSeat,
    ToolCallRecord,
)
from agent.application.errors import LedgerUnavailable, ModelUnavailable
from agent.domain.values import CaptureReading, CategoryChoice, Direction

from .read_capture import CANCELLED, NO_AMOUNT, QUESTION, UNREADABLE

_REFUSALS = {
    QUESTION: "question",
    CANCELLED: "cancelled",
    NO_AMOUNT: "no_amount",
    UNREADABLE: "unreadable",
}


def capture_run(run_id: str, text: str, reading: CaptureReading) -> RunRecord:
    """가맹점을 읽었으면 이어서 고른 카테고리를 `suggest_category` 한 건으로 남긴다."""
    calls: tuple[ToolCallRecord, ...] = ()
    if reading.category is not None and reading.merchant is not None:
        direction = reading.direction or Direction.EXPENSE  # 고를 때 쓴 방향(ReadCapture)
        calls = (_suggest(reading.merchant, "", direction, reading.category),)
    stop = _REFUSALS.get(reading.refusal, "refused") if reading.refusal else "read"
    return RunRecord(run_id, RunSeat.CAPTURE, text, stop, tool_calls=calls)


def classify_run(
    run_id: str, merchant: str, memo: str, direction: Direction, choice: CategoryChoice
) -> RunRecord:
    """끝난 이유는 고른 길이다 — rule·history·vector·llm, 고르지 않았으면 none."""
    utterance = "\n".join(part for part in (merchant, memo) if part.strip())
    calls = (_suggest(merchant, memo, direction, choice),) if utterance else ()
    return RunRecord(run_id, RunSeat.CLASSIFY, utterance, choice.strategy.value, tool_calls=calls)


def chat_run(run_id: str, question: str, outcome: LoopOutcome) -> RunRecord:
    """스텝마다 실제로 부른 호출(사전 검사로 고친 뒤)과 그 봉투."""
    calls: list[ToolCallRecord] = []
    seen: set[str] = set()
    for n, step in enumerate(outcome.steps, start=1):
        # call_id는 제공자가 정한다. 실행 안에서 겹치면 감사 키가 깨지니 순번을 붙인다
        call_id = step.call.call_id if step.call.call_id not in seen else f"{step.call.call_id}#{n}"
        seen.add(call_id)
        calls.append(
            ToolCallRecord(
                call_id, step.call.name, dict(step.call.arguments), step.result.envelope()
            )
        )
    return RunRecord(
        run_id,
        RunSeat.CHAT,
        question,
        outcome.stop.value,
        steps=outcome.model_calls,
        tokens=outcome.usage.input_tokens + outcome.usage.output_tokens,
        cost_usd=outcome.usage.cost_usd,
        tool_calls=tuple(calls),
    )


def ask_run(run_id: str, question: str, answer: DocumentAnswer) -> RunRecord:
    """찾기 한 번을 `search_documents` 한 건으로. 결과는 조각 id만 — 원문은 문서 테이블에 있다."""
    retrieval = answer.retrieval
    search = ToolCallRecord(
        "c1",
        "search_documents",
        {"q": question, "mode": retrieval.mode.value},
        {
            "fell_back": retrieval.fell_back,
            "chunk_ids": [c.id for c in retrieval.chunks],
            "cited_ids": [c.id for c in answer.citations],
        },
    )
    return RunRecord(run_id, RunSeat.ASK, question, answer.status.value, tool_calls=(search,))


def failed_run(run_id: str, seat: RunSeat, utterance: str, error: Exception) -> RunRecord:
    """503으로 끝난 실행. 끝난 이유는 닿지 못한 곳이다."""
    if isinstance(error, ModelUnavailable):
        stop = "model_unavailable"
    elif isinstance(error, LedgerUnavailable):
        stop = "ledger_unavailable"
    else:
        stop = "internal_error"
    return RunRecord(run_id, seat, utterance, stop, failed=True)


def _suggest(
    merchant: str, memo: str, direction: Direction, choice: CategoryChoice
) -> ToolCallRecord:
    return ToolCallRecord(
        "c1",
        "suggest_category",
        {"merchant": merchant, "memo": memo, "direction": direction.value},
        {
            "category_id": choice.category_id,
            "strategy": choice.strategy.value,
            "reason": choice.reason,
        },
    )
