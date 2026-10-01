from __future__ import annotations


class LedgerUnavailable(Exception):
    """api에 닿지 못했거나 api가 모르는 모양으로 답했다. 검색이 없으면 RAG도 없다."""
