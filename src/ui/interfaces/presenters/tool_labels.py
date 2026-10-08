"""SSE `tool` 이벤트의 도구 이름을 진행 줄 문구로. 도구 인자는 받지도 보이지도 않는다."""

from __future__ import annotations

_LABELS = {
    "search_transactions": "거래를 찾는 중…",
    "summarize_spending": "합계를 내는 중…",
    "count_frequency": "세는 중…",
    "compare_periods": "견주는 중…",
    "get_budget_status": "예산을 보는 중…",
    "suggest_category": "카테고리를 고르는 중…",
    "create_transaction": "기록을 준비하는 중…",
    "update_transaction": "기록을 고치는 중…",
    "delete_transaction": "기록을 지우는 중…",
    "set_budget": "예산을 정하는 중…",
}


def progress_label(tool: str) -> str:
    return _LABELS.get(tool, "생각하는 중…")
