from __future__ import annotations

from ui.application.dto import CategorySuggestion, Direction
from ui.application.values import CategoryId

# 키워드 → (카테고리, 방향). 진짜 api의 규칙 테이블이 이 자리에 온다.
_KEYWORDS: tuple[tuple[str, str, Direction], ...] = (
    ("김밥", "food", Direction.EXPENSE),
    ("도시락", "food", Direction.EXPENSE),
    ("국밥", "food", Direction.EXPENSE),
    ("본죽", "food", Direction.EXPENSE),
    ("맥도날드", "food", Direction.EXPENSE),
    ("서브웨이", "food", Direction.EXPENSE),
    ("치킨", "food", Direction.EXPENSE),
    ("배달", "food", Direction.EXPENSE),
    ("식당", "food", Direction.EXPENSE),
    ("점심", "food", Direction.EXPENSE),
    ("저녁", "food", Direction.EXPENSE),
    ("스타벅스", "cafe", Direction.EXPENSE),
    ("커피", "cafe", Direction.EXPENSE),
    ("카페", "cafe", Direction.EXPENSE),
    ("투썸", "cafe", Direction.EXPENSE),
    ("이디야", "cafe", Direction.EXPENSE),
    ("지하철", "transport", Direction.EXPENSE),
    ("버스", "transport", Direction.EXPENSE),
    ("택시", "transport", Direction.EXPENSE),
    ("카카오T", "transport", Direction.EXPENSE),
    ("주유", "transport", Direction.EXPENSE),
    ("이마트", "living", Direction.EXPENSE),
    ("쿠팡", "living", Direction.EXPENSE),
    ("다이소", "living", Direction.EXPENSE),
    ("올리브영", "living", Direction.EXPENSE),
    ("마트", "living", Direction.EXPENSE),
    ("월세", "housing", Direction.EXPENSE),
    ("관리비", "housing", Direction.EXPENSE),
    ("급여", "salary", Direction.INCOME),
    ("월급", "salary", Direction.INCOME),
)


class ScriptedCategorySuggester:
    """키 없이 도는 대역. 가맹점명에 든 낱말 하나로 고른다."""

    async def suggest(self, merchant: str, direction: Direction) -> CategorySuggestion | None:
        text = merchant.strip()
        for keyword, category_id, kind in _KEYWORDS:
            if kind == direction and keyword.lower() in text.lower():
                reason = f"각본 대역이 낸 값입니다 — '{keyword}'"
                return CategorySuggestion(CategoryId(category_id), reason)
        return None
