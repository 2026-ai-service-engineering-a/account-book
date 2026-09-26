from __future__ import annotations

import re
from datetime import time

from ui.application.dto import Direction

from .parsed_utterance import ParsedUtterance

_AMOUNT = re.compile(r"(\d[\d,]*)\s*(만)?\s*원")
_BARE_NUMBER = re.compile(r"(?<![\d,])(\d{1,3}(?:,\d{3})+|\d{3,})(?![\d,])")
_DAYS = {"그저께": -2, "그제": -2, "어제": -1, "오늘": 0}
_MEALS = {"아침": time(8, 30), "점심": time(12, 30), "저녁": time(19, 0), "야식": time(22, 0)}
_ACCOUNTS = {"카드": "card", "현금": "cash", "이체": "bank", "계좌": "bank"}
_INCOME_WORDS = ("급여", "월급", "입금", "받았")
_QUESTION_WORDS = ("얼마", "보여줘", "알려줘", "?")
_FILLERS = ("결제", "샀어", "썼어", "했어", "먹었어", "지난달", "이번", "달")
_PARTICLES = ("에서", "으로", "로", "에", "을", "를")


class UtteranceParser:
    """각본 대역의 귀. 정해진 모양의 한 줄만 알아듣는다.

    LLM이 들어오면 이 파일이 통째로 빠진다. 여기 규칙을 늘려 LLM 흉내를 내지 않는다.
    """

    def parse(self, text: str) -> ParsedUtterance:
        words = text.split()
        return ParsedUtterance(
            amount=_amount(text),
            day_offset=next((v for k, v in _DAYS.items() if k in text), 0),
            at=next((v for k, v in _MEALS.items() if k in text), None),
            account_id=next((v for k, v in _ACCOUNTS.items() if k in text), "card"),
            direction=(
                Direction.INCOME if any(w in text for w in _INCOME_WORDS) else Direction.EXPENSE
            ),
            merchant=next((w for w in map(_strip_particle, words) if _is_name(w)), ""),
            is_question=any(w in text for w in _QUESTION_WORDS),
            previous_month="지난달" in text or "지난 달" in text,
        )


def _amount(text: str) -> int | None:
    match = _AMOUNT.search(text)
    if match:
        value = int(match.group(1).replace(",", ""))
        return value * 10_000 if match.group(2) else value
    bare = _BARE_NUMBER.search(text)
    return int(bare.group(1).replace(",", "")) if bare else None


def _strip_particle(word: str) -> str:
    for particle in _PARTICLES:
        if word.endswith(particle) and len(word) > len(particle) + 1:
            return word[: -len(particle)]
    return word


def _is_name(word: str) -> bool:
    if any(ch.isdigit() for ch in word):
        return False
    known = (*_DAYS, *_MEALS, *_ACCOUNTS, *_FILLERS)
    return not any(k in word for k in known)
