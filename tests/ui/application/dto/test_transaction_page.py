from __future__ import annotations

from ui.application.dto import TransactionPage


def test_no_cursor_means_last_page():
    last = TransactionPage(items=(), next_cursor=None)
    assert last.next_cursor is None and last.items == ()
