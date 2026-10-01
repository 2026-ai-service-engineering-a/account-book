from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime, tzinfo

from ui.application.dto import (
    Category,
    CategorySuggestion,
    Direction,
    MessageReading,
    Transaction,
    TransactionDraft,
)
from ui.application.values import AccountId, CategoryId, Money

_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


@dataclass(slots=True)
class TransactionForm:
    """거래 폼의 날것 그대로의 값. 새로 넣기와 고치기가 같은 폼을 쓴다.

    여기서 하는 검사는 화면 편의다. 진짜 검증은 api가 한다(transaction-form.md 5장).
    """

    direction: str = Direction.EXPENSE.value
    amount: str = ""
    occurred_at: str = ""
    category_id: str = ""
    account_id: str = "card"
    merchant: str = ""
    memo: str = ""
    # 화면을 열 때 만든다. 제출할 때 만들면 새로고침 재제출이 새 키를 받는다.
    idempotency_key: str = ""

    @classmethod
    def blank(cls, now: datetime, account_id: str) -> TransactionForm:
        return cls(
            occurred_at=now.strftime(_LOCAL_FORMAT),
            account_id=account_id,
            idempotency_key=uuid.uuid4().hex,
        )

    @classmethod
    def of(cls, transaction: Transaction, zone: tzinfo) -> TransactionForm:
        return cls(
            direction=transaction.direction.value,
            amount=f"{transaction.amount:,}",
            occurred_at=transaction.occurred_at.astimezone(zone).strftime(_LOCAL_FORMAT),
            category_id=transaction.category_id,
            account_id=transaction.account_id,
            merchant=transaction.merchant,
            memo=transaction.memo,
            idempotency_key=uuid.uuid4().hex,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> TransactionForm:
        values = {f.name: data.get(f.name) for f in fields(cls)}
        return cls(**{k: v.strip() for k, v in values.items() if isinstance(v, str)})

    @property
    def direction_value(self) -> Direction:
        return Direction.INCOME if self.direction == Direction.INCOME.value else Direction.EXPENSE

    def parse(self, zone: tzinfo) -> tuple[TransactionDraft | None, dict[str, str]]:
        errors: dict[str, str] = {}
        digits = self.amount.replace(",", "").replace("원", "").strip()
        if not digits.isdigit():
            errors["amount"] = "금액을 숫자로 넣어 주세요."
        try:
            occurred = datetime.strptime(self.occurred_at, _LOCAL_FORMAT).replace(tzinfo=zone)
        except ValueError:
            errors["occurred_at"] = "날짜와 시각을 넣어 주세요."
        if not self.category_id:
            errors["category_id"] = "카테고리를 골라 주세요."
        if errors:
            return None, errors
        draft = TransactionDraft(
            direction=self.direction_value,
            amount=Money(int(digits)),
            occurred_at=occurred,
            category_id=CategoryId(self.category_id),
            account_id=AccountId(self.account_id),
            merchant=self.merchant,
            memo=self.memo,
        )
        return draft, {}

    def apply(self, reading: MessageReading, zone: tzinfo) -> frozenset[str]:
        """읽은 칸만 덮고, 덮은 칸 이름을 돌려준다. 화면이 그 칸에 표시를 단다.

        붙여넣기는 사용자가 채우라고 시킨 것이라 기존 값을 덮는다(transaction-form.md 4.4).
        금액을 못 읽었으면 아무 칸도 바꾸지 않는다.
        """
        if reading.refusal or reading.amount is None:
            return frozenset()
        filled = {"amount"}
        self.amount = f"{reading.amount:,}"
        if reading.direction is not None:
            self.direction = reading.direction.value
            filled.add("direction")
        if reading.occurred_at is not None:
            self.occurred_at = reading.occurred_at.astimezone(zone).strftime(_LOCAL_FORMAT)
            filled.add("occurred_at")
        if reading.account_id is not None:
            self.account_id = reading.account_id
            filled.add("account_id")
        if reading.merchant is not None:
            self.merchant = reading.merchant
            filled.add("merchant")
        return frozenset(filled)

    def drop_category_outside(self, categories: tuple[Category, ...]) -> None:
        """방향이 바뀌어 목록에 없는 카테고리는 비운다. 지출 목록에 "급여"가 남지 않게(3장)."""
        if self.category_id not in {c.id for c in categories}:
            self.category_id = ""

    def apply_suggestion(
        self,
        suggestion: CategorySuggestion,
        categories: tuple[Category, ...],
        *,
        overwrite: bool,
    ) -> frozenset[str]:
        """고른 카테고리를 넣고, 채웠으면 그 칸 이름을 돌려준다 — 화면이 표시를 단다.

        `overwrite`가 아니면 사용자가 고른 것을 덮지 않는다(transaction-form.md 4.1).
        AI 버튼은 누른 것이 동의라서 덮는다. 목록에 없는 값은 넣지 않는다.
        """
        chosen = suggestion.category_id
        if chosen is None or chosen not in {c.id for c in categories}:
            return frozenset()
        if self.category_id and not overwrite:
            return frozenset()
        self.category_id = chosen
        return frozenset({"category_id"})
