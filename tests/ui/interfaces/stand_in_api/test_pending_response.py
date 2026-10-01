from __future__ import annotations

from ui.interfaces.stand_in_api import PendingResponse


def test_shape():
    assert PendingResponse(items=[]).items == []
