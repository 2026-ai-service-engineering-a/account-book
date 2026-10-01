from __future__ import annotations

from tests.ui.infrastructure.api.conftest import TX
from ui.infrastructure.api import TransactionPageReply


def test_cursor_is_kept_opaque():
    page = TransactionPageReply.model_validate({"items": [TX], "next_cursor": "abc"}).page()
    assert page.next_cursor == "abc" and page.items[0].id == "t1"
    assert (
        TransactionPageReply.model_validate({"items": [], "next_cursor": None}).page().next_cursor
        is None
    )
