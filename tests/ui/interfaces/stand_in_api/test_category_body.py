from __future__ import annotations

from ui.interfaces.stand_in_api import CategoryBody


def test_shape():
    assert CategoryBody(id="cafe", name="카페").name == "카페"
