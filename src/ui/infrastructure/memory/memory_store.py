from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from zoneinfo import ZoneInfo

from ui.application.dto import (
    Account,
    Category,
    Direction,
    Transaction,
    TransactionDraft,
    TransactionFilter,
)
from ui.application.values import (
    AccountId,
    CategoryId,
    IdempotencyKey,
    Money,
    TextHash,
    TransactionId,
)

_CATEGORIES = (
    Category(CategoryId("food"), "식비", Direction.EXPENSE),
    Category(CategoryId("cafe"), "카페", Direction.EXPENSE),
    Category(CategoryId("transport"), "교통", Direction.EXPENSE),
    Category(CategoryId("living"), "생활", Direction.EXPENSE),
    Category(CategoryId("housing"), "주거", Direction.EXPENSE),
    Category(CategoryId("etc"), "기타", Direction.EXPENSE),
    Category(CategoryId("salary"), "급여", Direction.INCOME),
    Category(CategoryId("other_income"), "기타수입", Direction.INCOME),
)
_ACCOUNTS = (
    Account(AccountId("card"), "카드"),
    Account(AccountId("cash"), "현금"),
    Account(AccountId("bank"), "계좌이체"),
)
_MAX_AMOUNT = Money(10_000_000_000)


@dataclass(slots=True)
class MemoryStore:
    """api와 db의 자리에 서는 메모리 저장소. 프로세스가 끝나면 사라진다.

    검증과 집계를 여기서 하는 것은 이것이 api의 대역이기 때문이다. 화면 코드는
    이 파일을 모른다 — 포트만 안다.
    """

    zone: ZoneInfo
    categories: dict[CategoryId, Category]
    accounts: dict[AccountId, Account]
    transactions: dict[TransactionId, Transaction] = field(default_factory=dict)
    limits: dict[CategoryId, Money] = field(default_factory=dict)  # 월 예산
    # Idempotency-Key → 그 키로 처리한 대상의 id
    replies: dict[IdempotencyKey, str] = field(default_factory=dict)
    # transaction_embeddings의 자리. 거래가 아니라 색인 텍스트에 붙는다 — (모델, 텍스트 해시) → 벡터
    embeddings: dict[tuple[str, TextHash], tuple[float, ...]] = field(default_factory=dict)
    # category_rules의 자리 — 색인 텍스트에 든 패턴 → 카테고리. 시드는 비어 있다(규칙은 사용자의 것)
    rules: dict[str, CategoryId] = field(default_factory=dict)
    sequence: int = 0

    @classmethod
    def create(cls, zone: ZoneInfo) -> MemoryStore:
        return cls(
            zone=zone,
            categories={c.id: c for c in _CATEGORIES},
            accounts={a.id: a for a in _ACCOUNTS},
        )

    def next_id(self) -> TransactionId:
        self.sequence += 1
        return TransactionId(f"t{self.sequence:05d}")

    def clear(self) -> None:
        self.transactions.clear()
        self.limits.clear()
        self.replies.clear()

    def local_day(self, transaction: Transaction) -> date:
        return transaction.occurred_at.astimezone(self.zone).date()

    def matching(self, criteria: TransactionFilter) -> list[Transaction]:
        query = criteria.query.strip().lower()
        return [
            t
            for t in self.transactions.values()
            if criteria.period.contains(self.local_day(t))
            and (criteria.direction is None or t.direction == criteria.direction)
            and (criteria.category_id is None or t.category_id == criteria.category_id)
            and (not query or query in t.merchant.lower() or query in t.memo.lower())
        ]

    def validate(self, draft: TransactionDraft) -> dict[str, str]:
        """api의 validation_error details 자리. 필드 이름 → 사람이 읽을 문구."""
        errors: dict[str, str] = {}
        if draft.amount <= Money(0):
            errors["amount"] = "금액은 0보다 커야 합니다."
        elif draft.amount > _MAX_AMOUNT:
            errors["amount"] = "금액이 너무 큽니다."
        category = self.categories.get(draft.category_id)
        if category is None:
            errors["category_id"] = "카테고리를 골라 주세요."
        elif category.direction != draft.direction:
            errors["category_id"] = "방향에 맞는 카테고리가 아닙니다."
        if draft.account_id not in self.accounts:
            errors["account_id"] = "결제수단을 골라 주세요."
        if draft.occurred_at.tzinfo is None:
            errors["occurred_at"] = "시각에 타임존이 없습니다."
        return errors
