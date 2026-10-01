from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PendingText:
    """아직 벡터가 없는 색인 텍스트. 같은 텍스트의 거래 여럿이 이 하나를 나눠 쓴다."""

    text_hash: str
    text: str
