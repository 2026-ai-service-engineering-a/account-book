from __future__ import annotations

import asyncio
import logging

import pytest

from mcp_server.application.errors import LedgerRejected, LedgerUnavailable
from mcp_server.application.use_cases import CallTool
from mcp_server.domain.tools import ToolName
from tests.mcp_server.conftest import FakeLedger, FakeRunLog, Timer, call_tool

SUM = ToolName.SUMMARIZE_SPENDING


def call(tool: CallTool, args: dict[str, object], name: ToolName = SUM) -> dict[str, object]:
    return asyncio.run(tool(name, args, "Claude Desktop"))


def test_an_answer_is_an_envelope_and_one_audit_row():
    runs = FakeRunLog()
    envelope = call(call_tool(runs=runs, timer=Timer(step=0.01)), {"period": "this_month"})
    assert envelope["ok"] is True and envelope["call_id"] == "run-1"
    meta = envelope["meta"]
    assert isinstance(meta, dict) and meta["elapsed_ms"] == 10
    (entry,) = runs.entries
    assert (entry.run_id, entry.tool, entry.client) == (
        "run-1",
        "summarize_spending",
        "Claude Desktop",
    )
    assert entry.args == {"period": "this_month"} and entry.envelope == envelope


def test_bad_arguments_come_back_as_a_flag_the_model_can_fix():
    runs = FakeRunLog()
    envelope = call(call_tool(runs=runs), {"period": "저번 주"})
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "validation_error"  # type: ignore[index]
    assert envelope["error"]["retryable"] is True  # type: ignore[index]
    assert "period" in envelope["error"]["hint"]  # type: ignore[index]
    assert runs.entries[0].stop_reason == "validation_error"  # 고치라는 답도 감사에 남는다


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (LedgerRejected(422, "validation_error", {"from": "날짜"}), "validation_error", True),
        (LedgerRejected(404, "not_found", {}), "not_found", False),
        (LedgerRejected(403, "permission_denied", {}), "permission_denied", False),
        (LedgerUnavailable("ConnectError"), "internal_error", True),
    ],
)
def test_the_api_s_refusals_follow_the_translation_table(error, code, retryable):
    runs = FakeRunLog()
    envelope = call(call_tool(FakeLedger(error), runs), {"period": "this_month"})
    assert envelope["error"]["code"] == code  # type: ignore[index]
    assert envelope["error"]["retryable"] is retryable  # type: ignore[index]
    assert runs.entries[0].failed is (code == "internal_error")


def test_over_the_limit_the_api_is_not_called_and_nothing_is_recorded():
    ledger, runs = FakeLedger(), FakeRunLog()
    tool = call_tool(ledger, runs, per_minute=2)
    for _ in range(2):
        assert call(tool, {"period": "today"})["ok"] is True
    refused = call(tool, {"period": "today"})
    assert refused["ok"] is False
    assert refused["error"] == {
        "code": "rate_limited",
        "retryable": True,
        "hint": "분당 호출 상한을 넘었다. 60초 뒤에 다시 부른다",
        "retry_after_seconds": 60,
    }
    assert len(ledger.seen) == 2 and len(runs.entries) == 2


def test_a_failed_audit_does_not_hold_back_the_answer(caplog):
    with caplog.at_level(logging.WARNING):
        envelope = call(
            call_tool(runs=FakeRunLog(LedgerUnavailable("ConnectError"))), {"period": "today"}
        )
    assert envelope["ok"] is True
    assert "mcp run record failed run_id=run-1 code=unavailable" in caplog.text


def test_the_operational_log_has_no_amounts_or_arguments(caplog):
    with caplog.at_level(logging.INFO):
        call(call_tool(), {"period": "this_month", "merchant": "스타벅스"})
    assert "스타벅스" not in caplog.text and "412000" not in caplog.text
    assert "tool=summarize_spending ok=True" in caplog.text
