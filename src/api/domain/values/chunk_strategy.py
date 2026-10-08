from __future__ import annotations

from enum import StrEnum


class ChunkStrategy(StrEnum):
    """문서를 조각으로 나누는 방법. 셋을 다 만들어 두고 재서 고른다(docs/ai/document-rag.md 7.2)."""

    FIXED_500 = "fixed_500"  # 구조를 모른 채 500자씩 — 기준선
    PARAGRAPH = "paragraph"  # 항 하나(딸린 호·목 포함)가 조각 하나
    PARAGRAPH_ITEM = "paragraph_item"  # 항이되 1,000자가 넘으면 호마다. 조 제목·항 머리를 붙인다
