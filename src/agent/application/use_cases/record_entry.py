"""읽은 한 줄을 쓰기 칸으로, 그 칸을 감사 줄과 확인 카드로(docs/ai/chat-capture.md 3·6장).

못 읽은 칸은 기본값으로 두고 `unsure`로 밝힌다 — 카테고리는 기타, 결제수단은 카드, 날짜는 지금.
카드에서 고치는 칸은 없다. 틀리면 취소하고 폼으로 간다.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from agent.application.dto import RecordCard, RunRecord, RunSeat, ToolCallRecord
from agent.domain.tools import CreateTransactionInput, ToolName
from agent.domain.values import CaptureReading, CategoryChoice, CategoryId, Direction, PaymentMethod

ACCOUNT_NAMES = {
    PaymentMethod.CARD: "카드",
    PaymentMethod.CASH: "현금",
    PaymentMethod.BANK: "계좌이체",
}
_FALLBACK = {Direction.EXPENSE: CategoryId("etc"), Direction.INCOME: CategoryId("other_income")}


def entry_of(
    reading: CaptureReading, now: datetime
) -> tuple[CreateTransactionInput, tuple[str, ...]]:
    """거절하지 않은 읽기만 넘긴다(금액이 있다)."""
    assert reading.amount is not None
    direction = reading.direction or Direction.EXPENSE
    unsure: list[str] = []
    category = reading.category.category_id if reading.category else None
    if category is None:
        category, unsure = _FALLBACK[direction], [*unsure, "category"]
    if reading.payment_method is None:
        unsure.append("account")
    entry = CreateTransactionInput(
        direction=direction,
        amount=reading.amount,
        occurred_at=reading.occurred_at or now,
        category_id=category,
        account=reading.payment_method or PaymentMethod.CARD,
        merchant=reading.merchant or "",
    )
    return entry, tuple(unsure)


def entry_args(entry: CreateTransactionInput) -> dict[str, object]:
    """감사 줄의 `create_transaction` 인자 — 도구 스키마 그대로. 확인 때 이것으로 다시 만든다."""
    return {
        "direction": entry.direction.value,
        "amount": entry.amount.amount,
        "occurred_at": entry.occurred_at.isoformat(),
        "category_id": entry.category_id,
        "account": entry.account.value,
        "merchant": entry.merchant,
        "memo": entry.memo,
    }


def proposal_run(
    run_id: str, text: str, entry: CreateTransactionInput, choice: CategoryChoice | None
) -> RunRecord:
    """제안 = 감사 줄(awaiting_confirmation). 카테고리를 골랐으면 그 고르기가 첫 호출이다 —
    쓰기의 순번(seq)이 멱등 키 `{run_id}:{seq}`가 된다."""
    calls: list[ToolCallRecord] = []
    if choice is not None:
        calls.append(
            ToolCallRecord(
                "c1",
                ToolName.SUGGEST_CATEGORY.value,
                {"merchant": entry.merchant, "memo": "", "direction": entry.direction.value},
                {"category_id": choice.category_id, "strategy": choice.strategy.value},
            )
        )
    calls.append(
        ToolCallRecord(
            f"c{len(calls) + 1}", ToolName.CREATE_TRANSACTION.value, entry_args(entry), None
        )
    )
    return RunRecord(
        run_id, RunSeat.CAPTURE, text, "proposed", awaiting=True, tool_calls=tuple(calls)
    )


def card_of(
    run_id: str, entry: CreateTransactionInput, names: Mapping[str, str], unsure: tuple[str, ...]
) -> RecordCard:
    return RecordCard(
        proposal_id=run_id,
        occurred_on=entry.occurred_at.date(),
        category_name=names.get(entry.category_id, entry.category_id),
        direction=entry.direction,
        amount=entry.amount.amount,
        account_name=ACCOUNT_NAMES[entry.account],
        merchant=entry.merchant,
        unsure=unsure,
    )
