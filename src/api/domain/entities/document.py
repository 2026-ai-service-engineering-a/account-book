from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from api.domain.values import DocumentId


@dataclass(frozen=True, slots=True)
class Document:
    """문서 하나 — 지금은 법령 하나. 본문은 받은 그대로다. 고치지 않는다."""

    id: DocumentId
    title: str
    source: str  # 어디서 받았나
    mst: str  # 법령일련번호. 다시 받으면 바뀐다
    effective_date: date  # 시행일자 — 답 아래에 늘 붙인다
    body: str  # 조문들의 원문(Markdown)
