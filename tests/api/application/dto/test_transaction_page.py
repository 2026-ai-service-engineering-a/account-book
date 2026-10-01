from __future__ import annotations

from api.application.dto import TransactionPage


def test_last_page_has_no_cursor():
    assert TransactionPage((), None).next_cursor is None
