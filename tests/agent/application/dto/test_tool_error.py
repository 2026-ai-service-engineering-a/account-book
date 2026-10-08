from __future__ import annotations

from agent.application.dto import ToolError


def test_code_retryable_hint():
    error = ToolError("not_found", False, "없다")
    assert (error.code, error.retryable) == ("not_found", False)
