from __future__ import annotations

from mcp_server.application.dto import RunEntry


def entry(envelope: dict[str, object]) -> RunEntry:
    return RunEntry("r1", "summarize_spending", {}, envelope, "Claude")


def test_an_answer_is_done_and_answered():
    found = entry({"ok": True, "data": {}})
    assert (found.failed, found.stop_reason) == (False, "answered")


def test_a_correctable_failure_is_still_an_answer():
    found = entry({"ok": False, "error": {"code": "validation_error"}})
    assert (found.failed, found.stop_reason) == (False, "validation_error")


def test_only_an_unreachable_api_is_a_failure():
    found = entry({"ok": False, "error": {"code": "internal_error"}})
    assert (found.failed, found.stop_reason) == (True, "internal_error")
