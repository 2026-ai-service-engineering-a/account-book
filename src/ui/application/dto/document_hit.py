from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .chunk_strategy import ChunkStrategy


@dataclass(frozen=True, slots=True)
class DocumentHit:
    """찾은 조각 하나. `body`는 원문 그대로 — 화면은 이것을 인용으로 보인다."""

    id: str
    title: str  # 법령명
    effective_date: date  # 시행일자 — 인용 아래에 늘 붙인다
    strategy: ChunkStrategy
    heading: str
    body: str
    score: float  # 0~1
