from __future__ import annotations

from api.infrastructure.db.rows import IdempotencyKeyRow


def test_maps_the_idempotency_keys_table():
    assert IdempotencyKeyRow.__tablename__ == "idempotency_keys"


def test_empty_status_means_in_progress():
    assert IdempotencyKeyRow.__table__.c.status_code.nullable
