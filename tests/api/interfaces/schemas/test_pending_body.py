from __future__ import annotations

from api.interfaces.schemas import PendingBody


def test_shape():
    assert PendingBody(text_hash="h", text="t").text == "t"
