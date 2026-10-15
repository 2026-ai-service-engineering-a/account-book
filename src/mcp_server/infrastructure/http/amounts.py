"""금액은 정수 최소단위와 통화를 함께 낸다 — "8,500원" 같은 문자열을 만들지 않는다
(docs/ai/tools.md 3.2). agent의 도구 결과와 같은 모양이다."""

from __future__ import annotations

CURRENCY = "KRW"


def amount(value: int | None) -> dict[str, object] | None:
    return None if value is None else {"amount": value, "currency": CURRENCY}
