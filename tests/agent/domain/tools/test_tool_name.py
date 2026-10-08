from __future__ import annotations

from agent.domain.tools import Permission, ToolName

WRITES = {"create_transaction", "update_transaction", "delete_transaction", "set_budget"}


def test_writes_need_confirmation_and_delete_always():
    assert {t.value for t in ToolName if t.permission is not Permission.READ} == WRITES
    assert ToolName.DELETE_TRANSACTION.permission is Permission.WRITE_ALWAYS_CONFIRM
    assert ToolName.SET_BUDGET.permission is Permission.WRITE_CONFIRM


def test_reads_are_read():
    assert ToolName.COUNT_FREQUENCY.permission is Permission.READ
    assert ToolName.SUGGEST_CATEGORY.permission is Permission.READ
