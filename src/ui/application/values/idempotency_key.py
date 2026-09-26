from __future__ import annotations

from typing import NewType

# 쓰기 요청의 Idempotency-Key. 같은 키면 두 번 실행하지 않는다(api-contract 3장).
IdempotencyKey = NewType("IdempotencyKey", str)
