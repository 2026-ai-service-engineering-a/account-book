from __future__ import annotations

from ui.application.dto import RunFilter


def test_narrowed_only_when_a_seat_or_status_is_chosen():
    assert not RunFilter().is_narrowed
    assert RunFilter(seat="mcp").is_narrowed and RunFilter(status="failed").is_narrowed
