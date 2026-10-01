from __future__ import annotations

from enum import StrEnum


class Source(StrEnum):
    """누가 넣은 기록인가. 에이전트가 만든 기록은 언제나 구분돼야 한다(README 6장)."""

    MANUAL = "manual"
    AGENT = "agent"
    IMPORT = "import"  # CSV 가져오기 — api가 낼 수 있는 값이라 받아 둔다
