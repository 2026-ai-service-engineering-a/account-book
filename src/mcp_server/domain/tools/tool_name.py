from __future__ import annotations

from enum import StrEnum


class ToolName(StrEnum):
    """mcp가 부를 줄 아는 도구 — 집계 넷(docs/ai/mcp.md 3.1).

    쓰기도 개별 거래도 없다. 계약 파일에 이 밖의 이름이 있으면 뜨지 않는다 — 열린 표면이
    코드 모르게 늘지 않는다.
    """

    SUMMARIZE_SPENDING = "summarize_spending"
    COMPARE_PERIODS = "compare_periods"
    COUNT_FREQUENCY = "count_frequency"
    GET_BUDGET_STATUS = "get_budget_status"
