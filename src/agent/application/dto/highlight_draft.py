from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightDraft:
    """모델이 쓴 "눈에 띈 것" 한 줄. 숫자 검증과 금지어 검사를 지나야 화면에 간다."""

    text: str
    source: str  # 근거로 든 call_id — 사람이 읽는 표시다. 숫자 검증은 이번 실행 전체로 한다
