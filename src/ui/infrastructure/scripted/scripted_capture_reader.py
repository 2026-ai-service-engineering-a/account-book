from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta

from ui.application.dto import Direction, MessageReading
from ui.application.values import AccountId, Money

from .parsed_utterance import ParsedUtterance
from .utterance_parser import UtteranceParser

# 카드 문자는 흔한 카드사 승인 문자 한 모양만 읽는다. 말로 쓴 한 줄은 채팅 대역과 같은 귀로
# 읽는다. 진짜 AI가 오면 이 파일이 통째로 빠진다 — 규칙을 늘려 LLM 흉내를 내지 않는다.
_AMOUNT = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\s*원")
_WHEN = re.compile(r"(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})")
_MERCHANT_AFTER_WHEN = re.compile(r"\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}\s+(\S+)")
_RUNNING_TOTALS = ("누적", "잔액")
_CARD_MARKS = ("승인", "Web발신", "누적", "잔액", "일시불")

_CANCELLED = "승인 취소 문자는 아직 읽지 않아요. 원래 거래를 찾아 직접 고쳐 주세요."
_NO_AMOUNT = (
    "금액을 찾지 못했어요. 카드 문자를 붙여넣거나 '오늘 오후 3시 카페 5천원'처럼 적어 주세요."
)
_QUESTION = "질문은 채팅에서 물어 주세요. 여기는 기록을 채우는 칸이에요."


class ScriptedCaptureReader:
    """키 없이 도는 대역. 목 UI와 테스트가 이걸 쓴다.

    `delay`는 진짜 호출의 지연을 흉내 낸다. 화면의 "읽는 중…"이 보여야 확인이 된다.
    """

    def __init__(self, delay: float = 0.4) -> None:
        self._delay = delay
        self._ear = UtteranceParser()

    async def read(self, text: str, now: datetime) -> MessageReading:
        await asyncio.sleep(self._delay)
        if _is_card_message(text):
            return _read_card_message(text, now)
        return _read_sentence(self._ear.parse(text), now)


def _is_card_message(text: str) -> bool:
    return bool(_WHEN.search(text)) or any(mark in text for mark in _CARD_MARKS)


def _read_sentence(parsed: ParsedUtterance, now: datetime) -> MessageReading:
    if parsed.is_question:
        return MessageReading(refusal=_QUESTION)
    if parsed.amount is None:
        return MessageReading(refusal=_NO_AMOUNT)
    return MessageReading(
        direction=parsed.direction,
        amount=parsed.amount,
        occurred_at=_sentence_when(parsed, now),
        account_id=parsed.account_id,
        merchant=parsed.merchant or None,
    )


def _sentence_when(parsed: ParsedUtterance, now: datetime) -> datetime | None:
    """말하지 않은 날짜·시각은 채우지 않는다. 폼에 이미 있는 값(지금)이 남는다."""
    day = (now + timedelta(days=parsed.day_offset)).date()
    if parsed.at is not None:
        return datetime.combine(day, parsed.at, tzinfo=now.tzinfo)
    if parsed.day_offset:
        return datetime.combine(
            day, now.time().replace(hour=12, minute=0, second=0, microsecond=0), tzinfo=now.tzinfo
        )
    return now.replace(second=0, microsecond=0) if parsed.day_said else None


def _read_card_message(message: str, now: datetime) -> MessageReading:
    if "취소" in message:
        return MessageReading(refusal=_CANCELLED)
    amount = _card_amount(message)
    if amount is None:
        return MessageReading(refusal=_NO_AMOUNT)
    return MessageReading(
        direction=_direction(message),
        amount=amount,
        occurred_at=_card_when(message, now),
        account_id=_account(message),
        merchant=_merchant(message),
    )


def _card_amount(message: str) -> Money | None:
    for match in _AMOUNT.finditer(message):
        # "누적1,234,500원"·"잔액 ..."은 이 거래의 금액이 아니다
        before = message[max(0, match.start() - 3) : match.start()]
        if not any(word in before for word in _RUNNING_TOTALS):
            return Money(int(match.group(1).replace(",", "")))
    return None


def _account(message: str) -> AccountId | None:
    if (
        "카드" in message or "체크" in message
    ):  # "KB국민체크(5678)승인" — 체크카드는 카드라고 안 쓴다
        return AccountId("card")
    return AccountId("bank") if "입금" in message else None


def _direction(message: str) -> Direction | None:
    if "입금" in message:
        return Direction.INCOME
    if any(word in message for word in ("승인", "결제", "출금")):
        return Direction.EXPENSE
    return None


def _card_when(message: str, now: datetime) -> datetime | None:
    match = _WHEN.search(message)
    if not match:
        return None
    month, day, hour, minute = (int(g) for g in match.groups())
    try:
        found = now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        return None
    # 문자에는 연도가 없다. 기준 시각보다 뒤면 작년 문자다(12/31 문자를 1/2에 붙여넣는 경우).
    return found.replace(year=found.year - 1) if found > now else found


def _merchant(message: str) -> str | None:
    match = _MERCHANT_AFTER_WHEN.search(message)
    if not match or any(match.group(1).startswith(w) for w in _RUNNING_TOTALS):
        return None
    return match.group(1)
