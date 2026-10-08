from __future__ import annotations

from dataclasses import dataclass

from .category_line import CategoryLine
from .evidence_line import EvidenceLine
from .suggested_category import SuggestedCategory


@dataclass(frozen=True, slots=True)
class CategorySuggestion:
    """suggest_category의 답 — 후보, 근거, 그 방향의 카테고리 사전(ai/tools.md 4.1)."""

    strategy: str  # rule · history · vector · none
    candidates: tuple[SuggestedCategory, ...]
    evidence: tuple[EvidenceLine, ...]
    categories: tuple[CategoryLine, ...]
