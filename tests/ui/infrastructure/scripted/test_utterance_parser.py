from __future__ import annotations

from datetime import time

from ui.application.dto import Direction
from ui.application.values import Money
from ui.infrastructure.scripted.utterance_parser import UtteranceParser


def test_parses_the_readme_sentence():
    parsed = UtteranceParser().parse("어제 점심 김밥천국 8500원 카드로")
    assert parsed.amount == Money(8_500)
    assert parsed.day_offset == -1
    assert parsed.at == time(12, 30)
    assert parsed.account_id == "card"
    assert parsed.merchant == "김밥천국"
    assert parsed.direction == Direction.EXPENSE
    assert not parsed.is_question


def test_amount_forms():
    parser = UtteranceParser()
    assert parser.parse("스타벅스 5,800원").amount == Money(5_800)
    assert parser.parse("이마트 3만원 현금").amount == Money(30_000)
    assert parser.parse("택시 12000").amount == Money(12_000)


def test_income_and_question():
    parser = UtteranceParser()
    assert parser.parse("월급 3200000원 들어왔어").direction == Direction.INCOME
    question = parser.parse("지난달 카페에 얼마 썼어?")
    assert question.is_question and question.previous_month
