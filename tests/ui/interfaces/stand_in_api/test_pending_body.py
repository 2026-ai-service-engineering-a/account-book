from __future__ import annotations

from ui.interfaces.stand_in_api import PendingBody


def test_shape():
    assert PendingBody(text_hash="h", text="t").text == "t"
