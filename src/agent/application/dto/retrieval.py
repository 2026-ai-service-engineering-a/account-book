from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import SearchMode

from .retrieved_chunk import RetrievedChunk


@dataclass(frozen=True, slots=True)
class Retrieval:
    """찾기 한 번의 결과. 임베딩을 못 해 키워드로 물러섰으면 `fell_back`이 선다 — 화면이 밝힌다."""

    mode: SearchMode  # 실제로 쓴 방법
    fell_back: bool
    chunks: tuple[RetrievedChunk, ...]
