from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from agent.application.dto import ClassifyThresholds
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.use_cases import ClassifyCategory, ReadCapture
from agent.application.use_cases.read_capture import (
    CANCELLED,
    NO_AMOUNT,
    NO_CATEGORY,
    QUESTION,
    UNREADABLE,
)
from agent.domain.values import (
    CaptureReading,
    CategoryChoice,
    ChoiceStrategy,
    Direction,
    Money,
    PaymentMethod,
)
from tests.agent.conftest import NOW, SENTENCE, SEOUL, FakeLedger, FakeModel, extraction, search

CARD = "[Web발신]\n신한카드(1234)승인\n홍*동\n8,500원 일시불\n09/16 12:31 김밥천국\n누적1,234,500원"


def read(model: FakeModel, text: str = SENTENCE) -> CaptureReading:
    return asyncio.run(ReadCapture(model)(text, NOW))


def test_sentence_fills_fields_and_code_sets_the_date():
    reading = read(FakeModel(extraction()))
    assert reading.amount == Money(5000) and reading.direction is Direction.EXPENSE
    assert reading.occurred_at == datetime(2026, 10, 1, 15, 0, tzinfo=SEOUL)
    assert reading.merchant == "카페" and reading.payment_method is None


def test_card_message():
    answer = extraction(
        amount=8500, payment="card", merchant="김밥천국", day="date", month=9, day_of_month=16
    ) | {"hour": 12, "minute": 31}
    reading = read(FakeModel(answer), CARD)
    assert reading.payment_method is PaymentMethod.CARD and reading.merchant == "김밥천국"
    assert reading.occurred_at == datetime(2026, 9, 16, 12, 31, tzinfo=SEOUL)


def test_the_text_goes_to_the_model_fenced():
    model = FakeModel(extraction())
    read(model)
    assert model.prompts[0].user == f"<<<DATA\n{SENTENCE}\nDATA>>>"


@pytest.mark.parametrize(
    ("kind", "refusal"),
    [("question", QUESTION), ("cancellation", CANCELLED), ("unreadable", NO_AMOUNT)],
)
def test_non_records_fill_nothing(kind, refusal):
    assert read(FakeModel(extraction(kind=kind))) == CaptureReading.refused(refusal)


def test_no_amount_fills_nothing():
    assert read(FakeModel(extraction(amount=0))) == CaptureReading.refused(NO_AMOUNT)


def test_absurd_amount_fills_nothing():
    reading = read(FakeModel(extraction(amount=99_000_000_000)))
    assert reading == CaptureReading.refused(NO_AMOUNT)


def test_made_up_merchant_is_dropped():
    # 보낸 글에 없는 가맹점은 모델이 지어낸 것이다. 다른 칸은 그대로 쓴다
    reading = read(FakeModel(extraction(merchant="스타벅스")))
    assert reading.merchant is None and reading.amount == Money(5000)


def test_merchant_spacing_differences_still_ground():
    reading = read(FakeModel(extraction(merchant="김밥 천국")), "어제 김밥천국 8천원")
    assert reading.merchant == "김밥 천국"


def test_malformed_once_is_asked_again():
    model = FakeModel(extraction(amount="오천"), extraction())
    assert read(model).amount == Money(5000) and len(model.prompts) == 2


def test_malformed_twice_is_dropped():
    model = FakeModel(MalformedOutput("x"), extraction(kind="maybe"))
    assert read(model) == CaptureReading.refused(UNREADABLE)


def test_unavailable_is_not_retried():
    model = FakeModel(ModelUnavailable("Timeout"))
    with pytest.raises(ModelUnavailable):
        read(model)
    assert len(model.prompts) == 1


def test_needs_an_aware_now():
    with pytest.raises(ValueError):
        asyncio.run(ReadCapture(FakeModel())(SENTENCE, datetime(2026, 10, 1)))


def read_with_category(model: FakeModel, ledger: FakeLedger) -> CaptureReading:
    classify = ClassifyCategory(ledger, model, ClassifyThresholds(0.7, 0.25))
    return asyncio.run(ReadCapture(model, classify)(SENTENCE, NOW))


def test_reading_a_merchant_goes_on_to_pick_a_category():
    ledger = FakeLedger(search(candidates=(("cafe", 0.9),)))
    reading = read_with_category(FakeModel(extraction()), ledger)
    assert reading.category is not None and reading.category.category_id == "cafe"
    assert reading.category.strategy is ChoiceStrategy.VECTOR
    assert ledger.queries[0].merchant == "카페" and ledger.queries[0].direction is Direction.EXPENSE


def test_no_merchant_no_category():
    ledger = FakeLedger()
    reading = read_with_category(FakeModel(extraction(merchant="")), ledger)
    assert reading.category is None and ledger.queries == []


def test_unknown_direction_is_classified_as_expense():
    ledger = FakeLedger(search())
    read_with_category(FakeModel(extraction(direction="unknown")), ledger)
    assert ledger.queries[0].direction is Direction.EXPENSE


def test_category_failure_keeps_the_values():
    reading = read_with_category(FakeModel(extraction()), FakeLedger(LedgerUnavailable("x")))
    assert reading.amount == Money(5000)
    assert reading.category == CategoryChoice.abstain(NO_CATEGORY)
