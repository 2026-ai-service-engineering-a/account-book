from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import CategoryId


@dataclass(frozen=True, slots=True)
class CategorySuggestion:
    category_id: CategoryId
    reason: str  # 화면에는 내지 않는다. 대역인지 진짜인지 로그·테스트에서 구분한다
