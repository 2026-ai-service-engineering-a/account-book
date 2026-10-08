from __future__ import annotations

from agent.application.dto import ToolMeta


def test_no_periods_and_no_note_by_default():
    meta = ToolMeta(row_count=1, truncated=False, elapsed_ms=3)
    assert meta.periods == {} and meta.note == ""
