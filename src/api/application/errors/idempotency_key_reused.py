from __future__ import annotations


class IdempotencyKeyReused(Exception):
    """같은 키로 다른 본문이 왔다. 409 idempotency_key_reused(api-contract 3장)."""
