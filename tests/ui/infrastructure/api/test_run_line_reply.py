from __future__ import annotations

from decimal import Decimal

from ui.infrastructure.api.run_line_reply import RunLineReply

LINE = {
    "id": "r1", "seat": "mcp", "flow": "direct", "utterance": "", "model": "external",
    "steps": 0, "tokens": 0, "cost_usd": "0.000000", "status": "done",
    "stop_reason": "answered", "client": "Claude", "created_at": "2026-10-15T04:57:00Z",
    "tool_count": 1,
}  # fmt: skip


def test_reads_a_line_and_keeps_the_count():
    line = RunLineReply.model_validate(LINE).line()
    assert (line.client, line.cost_usd, line.tool_count) == ("Claude", Decimal(0), 1)
    assert RunLineReply.model_validate(LINE).line(tool_count=3).tool_count == 3
