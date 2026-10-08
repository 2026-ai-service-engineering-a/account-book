from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agent.domain.values import ChunkStrategy


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """api가 찾아 준 조각 하나. `body`는 원문 — 화면의 인용이고, 생성에서는 DATA 마커 안에 든다."""

    id: str
    title: str  # 법령명
    effective_date: date
    strategy: ChunkStrategy
    heading: str
    body: str
    score: float  # 방법마다 뜻이 다르다 — 키워드·벡터는 0~1, 하이브리드는 RRF 점수
