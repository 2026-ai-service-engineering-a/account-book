from __future__ import annotations

import re
from datetime import time

from ui.application.dto import Direction
from ui.application.values import AccountId, Money

from .parsed_utterance import ParsedUtterance

# "5천원" · "1만5천원" · "3만원" · "8500원". 천 단위 쉼표는 먼저 지운다.
_UNIT_AMOUNT = re.compile(r"(?:(\d+)\s*만)?\s*(?:(\d+)\s*천)?\s*(\d+)?\s*원")
_BARE_NUMBER = re.compile(r"(?<![\d,])(\d{1,3}(?:,\d{3})+|\d{3,})(?![\d,])")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3})")
_CLOCK = re.compile(
    r"(오전|오후|새벽|아침|낮|저녁|밤)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분|\s*(반))?"
)
_AFTERNOON = ("오후", "낮", "저녁", "밤")
_DAYS = {"그저께": -2, "그제": -2, "어제": -1, "오늘": 0}
_MEALS = {"아침": time(8, 30), "점심": time(12, 30), "저녁": time(19, 0), "야식": time(22, 0)}
_ACCOUNTS = {"카드": "card", "현금": "cash", "이체": "bank", "계좌": "bank"}
_INCOME_WORDS = ("급여", "월급", "입금", "받았", "들어왔")
_QUESTION_WORDS = ("얼마", "보여줘", "알려줘", "?")
_FILLERS = (
    "결제",
    "샀어",
    "썼어",
    "했어",
    "먹었어",
    "지난달",
    "이번",
    "달",
    "오전",
    "오후",
    "새벽",
    "낮",
    "밤",
)
_PARTICLES = ("에서", "으로", "로", "에", "을", "를")


class UtteranceParser:
    """각본 대역의 귀. 정해진 모양의 한 줄만 알아듣는다.

    LLM이 들어오면 이 파일이 통째로 빠진다. 여기 규칙을 늘려 LLM 흉내를 내지 않는다.
    알아듣는 모양은 ui_docs/stand-ins.md 1장에 적어 둔 것뿐이다.
    """

    def parse(self, text: str) -> ParsedUtterance:
        words = text.split()
        names = [w for w in map(_strip_particle, words) if _is_name(w)]
        # "카페에서"처럼 장소 조사가 붙은 낱말이 가맹점일 가능성이 가장 높다
        place = next((w[:-2] for w in words if w.endswith("에서") and _is_name(w[:-2])), "")
        account = next((v for k, v in _ACCOUNTS.items() if k in text), None)
        return ParsedUtterance(
            amount=_amount(text),
            day_offset=next((v for k, v in _DAYS.items() if k in text), 0),
            day_said=any(k in text for k in _DAYS),
            at=_clock(text) or next((v for k, v in _MEALS.items() if k in text), None),
            account_id=AccountId(account) if account else None,
            direction=(
                Direction.INCOME if any(w in text for w in _INCOME_WORDS) else Direction.EXPENSE
            ),
            merchant=place or (names[0] if names else ""),
            is_question=any(w in text for w in _QUESTION_WORDS),
            previous_month="지난달" in text or "지난 달" in text,
        )


def _amount(text: str) -> Money | None:
    plain = _THOUSANDS.sub("", text)
    for match in _UNIT_AMOUNT.finditer(plain):
        man, cheon, rest = (int(g) if g else 0 for g in match.groups())
        value = man * 10_000 + cheon * 1_000 + rest
        if value:
            return Money(value)
    bare = _BARE_NUMBER.search(text)
    return Money(int(bare.group(1).replace(",", ""))) if bare else None


def _clock(text: str) -> time | None:
    match = _CLOCK.search(text)
    if not match:
        return None
    meridiem, hour_text, minute_text, half = match.groups()
    hour, minute = int(hour_text), int(minute_text) if minute_text else (30 if half else 0)
    # "3시"처럼 오전·오후를 말하지 않은 1~6시는 낮으로 본다. 새벽 3시에 카페에 가는 일은 드물다.
    if (meridiem in _AFTERNOON or (meridiem is None and 1 <= hour <= 6)) and hour < 12:
        hour += 12
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def _strip_particle(word: str) -> str:
    for particle in _PARTICLES:
        if word.endswith(particle) and len(word) > len(particle) + 1:
            return word[: -len(particle)]
    return word


def _is_name(word: str) -> bool:
    if not word or any(ch.isdigit() for ch in word):
        return False
    known = (*_DAYS, *_MEALS, *_ACCOUNTS, *_FILLERS)
    return not any(k in word for k in known)
