from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Direction


@dataclass(frozen=True, slots=True)
class SuggestCategoryInput:
    merchant: str
    memo: str = ""
    direction: Direction = Direction.EXPENSE

    def __post_init__(self) -> None:
        if not (self.merchant.strip() or self.memo.strip()):
            raise ValueError("가맹점이나 메모 중 하나는 있어야 한다")
