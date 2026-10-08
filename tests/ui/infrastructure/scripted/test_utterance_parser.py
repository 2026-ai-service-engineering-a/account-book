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
    assert parsed.day_said
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
    assert question.is_question and question.previous_month and not question.other_period


def test_periods_beyond_this_and_last_month_are_flagged():
    parser = UtteranceParser()
    for text in ("8월 식비는?", "10월 식비 얼마", "지지난 달 식비", "저번 주 카페", "올해 얼마"):
        assert parser.parse(text).other_period, text
    for text in ("이번 달 식비 얼마 썼어?", "지난 달 주거 얼마?", "월급 얼마 들어왔어?"):
        assert not parser.parse(text).other_period, text


def test_korean_units_and_clock():
    parser = UtteranceParser()
    parsed = parser.parse("오늘 오후 3시에 카페에서 5천원 썼어")
    assert (parsed.amount, parsed.at, parsed.merchant) == (Money(5_000), time(15, 0), "카페")
    assert parser.parse("1만5천원 택시").amount == Money(15_000)
    assert parser.parse("오전 9시 반 편의점 3,200원").at == time(9, 30)
    assert parser.parse("3시 편의점 1000원").at == time(15, 0)  # 오전·오후가 없으면 낮으로


def test_unsaid_account_and_day_stay_empty():
    parsed = UtteranceParser().parse("편의점 1,200원")
    assert parsed.account_id is None and not parsed.day_said
