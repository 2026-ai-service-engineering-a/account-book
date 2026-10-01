from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import CategoryId


@dataclass(frozen=True, slots=True)
class CategorySuggestion:
    """카테고리 고르기의 결과. `category_id`가 None이면 고르지 못했고, 셀렉트는 그대로 둔다.

    `reason`은 셀렉트 아래에 그대로 보일 근거 한 줄이다(docs/ai/category-suggestion-rag.md 8.1).
    이유 없이 값이 바뀌면 사람이 검사할 방법이 없다.
    """

    category_id: CategoryId | None
    reason: str
    by_llm: bool = False  # LLM이 골랐으면 근거 줄에 AI 표시를 단다(7장 표)
