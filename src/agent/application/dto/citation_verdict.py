from __future__ import annotations

from enum import StrEnum


class CitationVerdict(StrEnum):
    """인용 검증의 결과(docs/ai/document-rag.md 5.3). 걸리면 답을 버린다 — 고쳐서 내지 않는다."""

    OK = "ok"
    UNKNOWN = "unknown"  # 넘겨주지 않은 조각을 인용했다
    MISSING = "missing"  # 인용이 없다
    NUMBERS = "numbers"  # 답의 숫자가 인용한 조각(과 허용된 숫자)에 없다
