from __future__ import annotations

from tests.ui.infrastructure.api.test_run_line_reply import LINE
from ui.infrastructure.api.run_detail_reply import RunDetailReply

CALL = {
    "call_id": "c1", "tool": "summarize_spending", "args": {"period": "this_month"},
    "result": {"ok": True, "data": {}}, "confirmed_at": None,
}  # fmt: skip


def test_the_count_is_the_number_of_calls():
    body = {k: v for k, v in LINE.items() if k != "tool_count"} | {"tool_calls": [CALL, CALL]}
    detail = RunDetailReply.model_validate(body).detail()
    assert detail.line.tool_count == 2 and detail.calls[0].args == {"period": "this_month"}
