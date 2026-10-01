from __future__ import annotations

from api.application.dto import IdempotencyRecord


def test_no_reply_means_in_progress():
    assert IdempotencyRecord("hash", None).reply is None
