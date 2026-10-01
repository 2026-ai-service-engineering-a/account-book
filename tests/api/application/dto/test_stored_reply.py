from __future__ import annotations

from api.application.dto import StoredReply


def test_delete_has_no_body():
    assert StoredReply(204).body is None
