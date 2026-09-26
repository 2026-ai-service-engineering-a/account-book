from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CategorySuggestion:
    category_id: str
    reason: str  # 화면에는 내지 않는다. 대역인지 진짜인지 로그·테스트에서 구분한다
