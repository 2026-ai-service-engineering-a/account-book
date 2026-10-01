"""LLM이 낸 JSON을 `CaptureExtraction`으로. `Any`(모양을 모르는 값)는 여기서 끝난다."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from agent.application.dto import CaptureExtraction, ExtractionKind
from agent.application.errors import MalformedOutput
from agent.domain.values import Direction, PaymentMethod, SaidDay, SaidWhen

_UNKNOWN = "unknown"
# 가맹점명이 이보다 길면 문장을 통째로 옮긴 것이다
_MERCHANT_LIMIT = 40


def parse_capture_extraction(raw: Mapping[str, object]) -> CaptureExtraction:
    """키 하나라도 모양이 틀리면 `MalformedOutput` — 부르는 쪽이 한 번 다시 시킨다."""
    hour = _integer(raw, "hour")
    try:
        when = SaidWhen(
            day=_choice(raw, "day", SaidDay),
            month=_integer(raw, "month"),
            day_of_month=_integer(raw, "day_of_month"),
            hour=None if hour < 0 else hour,
            minute=_integer(raw, "minute") if hour >= 0 else 0,
        )
    except ValueError as error:
        raise MalformedOutput(f"날짜·시각이 아니다: {error}") from error
    amount = _integer(raw, "amount")
    if amount < 0:
        raise MalformedOutput("금액이 음수다")
    return CaptureExtraction(
        kind=_choice(raw, "kind", ExtractionKind),
        amount=amount,
        direction=_optional_choice(raw, "direction", Direction),
        payment_method=_optional_choice(raw, "payment", PaymentMethod),
        merchant=_string(raw, "merchant").strip()[:_MERCHANT_LIMIT],
        when=when,
    )


def _integer(raw: Mapping[str, object], key: str) -> int:
    value = raw.get(key)
    # JSON에는 정수와 실수의 구분이 없다. 5000.0은 받고 5000.5는 버린다.
    # bool은 int의 하위형이라 따로 거른다.
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedOutput(f"{key}가 정수가 아니다")
    return value


def _string(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise MalformedOutput(f"{key}가 문자열이 아니다")
    return value


def _choice[E: StrEnum](raw: Mapping[str, object], key: str, kind: type[E]) -> E:
    value = _string(raw, key)
    try:
        return kind(value)
    except ValueError as error:
        raise MalformedOutput(f"{key}가 정해진 값이 아니다") from error


def _optional_choice[E: StrEnum](raw: Mapping[str, object], key: str, kind: type[E]) -> E | None:
    return None if raw.get(key) == _UNKNOWN else _choice(raw, key, kind)
