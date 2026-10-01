from __future__ import annotations

from api.application.errors import IdempotencyKeyReused, RequestInProgress


def test_is_its_own_case():
    assert not issubclass(RequestInProgress, IdempotencyKeyReused)
