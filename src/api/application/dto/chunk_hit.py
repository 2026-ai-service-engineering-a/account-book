from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from api.domain.entities import DocumentChunk


@dataclass(frozen=True, slots=True)
class ChunkHit:
    """검색이 찾은 조각 하나와 그 점수. 출처를 붙이려고 문서의 제목과 시행일자를 같이 든다."""

    chunk: DocumentChunk
    score: float  # 0~1. 키워드 검색이면 pg_trgm의 word_similarity
    title: str
    effective_date: date
