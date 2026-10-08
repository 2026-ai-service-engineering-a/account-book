from __future__ import annotations

from dataclasses import dataclass

from .document_hit import DocumentHit
from .search_mode import SearchMode


@dataclass(frozen=True, slots=True)
class DocumentResults:
    """찾기 한 번 — 조각과, 실제로 쓴 방법. 물러섰으면 화면이 그 사실을 밝힌다."""

    hits: tuple[DocumentHit, ...]
    mode: SearchMode
    fell_back: bool = False  # 고른 방법을 못 써서 낱말로 찾았다
