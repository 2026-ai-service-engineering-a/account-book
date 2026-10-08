from __future__ import annotations

from enum import StrEnum

from .permission import Permission


class ToolName(StrEnum):
    """에이전트 도구의 이름 — 목록이 곧 능력 범위다(README 4장).

    쓰기 넷은 이름과 권한만 있다. 스키마는 쓰는 feature에서 붙인다. 이름이 여기 있어야
    "query 모드에 쓰기 도구가 없다"를 검사할 수 있다.
    """

    SEARCH_TRANSACTIONS = "search_transactions"
    SUMMARIZE_SPENDING = "summarize_spending"
    COUNT_FREQUENCY = "count_frequency"
    COMPARE_PERIODS = "compare_periods"
    GET_BUDGET_STATUS = "get_budget_status"
    SUGGEST_CATEGORY = "suggest_category"
    SEARCH_DOCUMENTS = "search_documents"
    CREATE_TRANSACTION = "create_transaction"
    UPDATE_TRANSACTION = "update_transaction"
    DELETE_TRANSACTION = "delete_transaction"
    SET_BUDGET = "set_budget"

    @property
    def permission(self) -> Permission:
        return _PERMISSIONS.get(self, Permission.READ)


_PERMISSIONS = {
    ToolName.CREATE_TRANSACTION: Permission.WRITE_CONFIRM,
    ToolName.UPDATE_TRANSACTION: Permission.WRITE_CONFIRM,
    ToolName.DELETE_TRANSACTION: Permission.WRITE_ALWAYS_CONFIRM,
    ToolName.SET_BUDGET: Permission.WRITE_CONFIRM,
}
