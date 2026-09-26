from __future__ import annotations

import asyncio
from datetime import datetime

from tests.ui.conftest import NOW, SEOUL
from ui.application.dto import Direction, MessageReading
from ui.application.values import AccountId, Money
from ui.infrastructure.scripted import ScriptedCardMessageReader

SHINHAN = (
    "[Web발신]\n신한카드(1234)승인\n홍*동\n8,500원 일시불\n09/16 12:31 김밥천국\n누적1,234,500원"
)


def read(message: str, now: datetime = NOW) -> MessageReading:
    return asyncio.run(ScriptedCardMessageReader(delay=0).read(message, now))


def test_reads_card_approval():
    reading = read(SHINHAN)
    assert reading.refusal == ""
    assert (reading.direction, reading.amount, reading.account_id, reading.merchant) == (
        Direction.EXPENSE,
        Money(8_500),
        AccountId("card"),
        "김밥천국",
    )
    assert reading.occurred_at == datetime(2026, 9, 16, 12, 31, tzinfo=SEOUL)


def test_running_total_is_not_the_amount():
    assert read("누적1,234,500원 KB국민카드 승인 12,000원 09/15 08:10 스타벅스").amount == Money(
        12_000
    )


def test_date_without_year_goes_back_a_year_when_in_future():
    reading = read(SHINHAN.replace("09/16", "12/30"))
    assert reading.occurred_at is not None and reading.occurred_at.year == 2025


def test_missing_parts_stay_empty():
    reading = read("현대카드 승인 5,800원")
    assert (reading.amount, reading.occurred_at, reading.merchant) == (Money(5_800), None, None)


def test_deposit_is_income():
    reading = read("[입금] 3,200,000원 09/10 09:00 회사급여 잔액 4,000,000원")
    assert (reading.direction, reading.account_id) == (Direction.INCOME, "bank")


def test_refuses_cancellation_and_no_amount():
    assert "취소" in read("신한카드 승인취소 8,500원 09/16 12:31 김밥천국").refusal
    refused = read("오늘 저녁 뭐 먹지")
    assert refused.refusal and refused.amount is None


def test_check_card_is_a_card():
    assert read("KB국민체크(5678)승인 12,000원 09/25 08:10 스타벅스").account_id == "card"
