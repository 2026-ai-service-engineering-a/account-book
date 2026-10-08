from __future__ import annotations

from enum import StrEnum


class ChunkStrategy(StrEnum):
    """api가 문서를 조각으로 나눈 방법. agent는 고르기만 한다 — 나누는 일은 api가 한다."""

    FIXED_500 = "fixed_500"
    PARAGRAPH = "paragraph"
    PARAGRAPH_ITEM = "paragraph_item"
