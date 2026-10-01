from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import TextHash


@dataclass(frozen=True, slots=True)
class IndexText:
    """아직 임베딩이 없는 색인 텍스트 하나. agent가 당겨 가서 벡터로 바꾼다."""

    text_hash: TextHash
    text: str
