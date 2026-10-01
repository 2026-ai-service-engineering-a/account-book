from __future__ import annotations


class MissingIdempotencyKey(Exception):
    """쓰기 요청에 `Idempotency-Key`가 없다. 400 idempotency_key_required(api-contract 3장)."""
