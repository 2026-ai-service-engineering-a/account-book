from __future__ import annotations

from enum import StrEnum


class ChunkStrategy(StrEnum):
    """문서를 조각으로 나눈 방법. api가 셋을 다 넣어 두고, 화면이 하나를 골라 찾는다."""

    PARAGRAPH = "paragraph"
    PARAGRAPH_ITEM = "paragraph_item"
    FIXED_500 = "fixed_500"

    @property
    def label(self) -> str:
        return _LABELS[self]


_LABELS = {
    ChunkStrategy.PARAGRAPH: "항 단위",
    ChunkStrategy.PARAGRAPH_ITEM: "항 · 긴 항은 호 단위",
    ChunkStrategy.FIXED_500: "500자씩(기준선)",
}
