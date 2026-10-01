from __future__ import annotations

from dataclasses import dataclass

from .category_id import CategoryId
from .choice_strategy import ChoiceStrategy


@dataclass(frozen=True, slots=True)
class CategoryChoice:
    """카테고리 고르기의 결과. `category_id`가 None이면 고르지 않았다(abstain).

    `reason`은 화면에 그대로 보일 한 줄이다. 근거 없이 값이 바뀌면 사람이 검사할 수 없다.
    """

    category_id: CategoryId | None
    strategy: ChoiceStrategy
    reason: str

    def __post_init__(self) -> None:
        if (self.category_id is None) != (self.strategy is ChoiceStrategy.NONE):
            raise ValueError("고르지 않았으면 NONE이고, NONE이면 고르지 않았다")

    @classmethod
    def abstain(cls, reason: str) -> CategoryChoice:
        return cls(None, ChoiceStrategy.NONE, reason)
