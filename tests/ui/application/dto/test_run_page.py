from __future__ import annotations

from ui.application.dto import RunPage


def test_last_page_has_no_cursor():
    assert RunPage((), None).next_cursor is None
