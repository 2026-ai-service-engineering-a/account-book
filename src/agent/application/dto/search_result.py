from __future__ import annotations

from dataclasses import dataclass

from .candidate import Candidate
from .category_entry import CategoryEntry
from .evidence import Evidence
from .search_strategy import SearchStrategy


@dataclass(frozen=True, slots=True)
class SearchResult:
    """api `POST /v1/categories/suggest`의 답. 후보는 신뢰도 높은 순이다."""

    strategy: SearchStrategy
    query_text: str
    needs_query_vector: bool
    candidates: tuple[Candidate, ...]
    evidence: tuple[Evidence, ...]
    categories: tuple[CategoryEntry, ...]

    def name_of(self, category_id: str) -> str:
        return next((c.name for c in self.categories if c.id == category_id), category_id)
