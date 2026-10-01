"""거래 값의 규칙. 화면이 먼저 보지만 진짜 검증은 여기다(ui_docs/pages/transaction-form.md 5장)."""

from __future__ import annotations

from api.application.dto import TransactionDraft
from api.application.ports import CatalogRepository
from api.domain.errors import InvalidTransaction

# 한 건에 백억 원을 넘는 가계부 기록은 없다
_MAX_AMOUNT = 10_000_000_000
_MERCHANT_LIMIT = 100
_MEMO_LIMIT = 200


def check_draft(draft: TransactionDraft, catalog: CatalogRepository) -> None:
    """걸린 것을 전부 모아 한 번에 낸다 — 화면이 필드 옆마다 표시한다. 문구는 사람이 읽는다."""
    errors: dict[str, str] = {}
    if draft.amount.amount <= 0:
        errors["amount"] = "금액은 0보다 커야 합니다."
    elif draft.amount.amount > _MAX_AMOUNT:
        errors["amount"] = "금액이 너무 큽니다."
    category = next((c for c in catalog.categories() if c.id == draft.category_id), None)
    if category is None:
        errors["category_id"] = "카테고리를 골라 주세요."
    elif category.direction != draft.direction:
        errors["category_id"] = "방향에 맞는 카테고리가 아닙니다."
    if draft.account_id not in {a.id for a in catalog.accounts()}:
        errors["account_id"] = "결제수단을 골라 주세요."
    if draft.occurred_at.tzinfo is None:
        errors["occurred_at"] = "시각에 타임존이 없습니다."
    if len(draft.merchant.strip()) > _MERCHANT_LIMIT:
        errors["merchant"] = f"가맹점은 {_MERCHANT_LIMIT}자까지입니다."
    if len(draft.memo.strip()) > _MEMO_LIMIT:
        errors["memo"] = f"메모는 {_MEMO_LIMIT}자까지입니다."
    if errors:
        raise InvalidTransaction(errors)
