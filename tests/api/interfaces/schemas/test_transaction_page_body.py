from __future__ import annotations

from api.application.dto import TransactionPage
from api.interfaces.schemas import TransactionPageBody


def test_empty_last_page():
    assert TransactionPageBody.of(TransactionPage((), None)).model_dump() == {
        "items": [],
        "next_cursor": None,
    }
