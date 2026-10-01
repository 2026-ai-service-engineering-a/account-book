from __future__ import annotations

from api.interfaces.schemas import PendingResponse


def test_shape():
    assert PendingResponse(items=[]).items == []
