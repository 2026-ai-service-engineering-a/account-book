from __future__ import annotations

import pytest

from agent.application.dto import ExtractionKind
from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_capture_extraction
from agent.domain.values import Direction, PaymentMethod, SaidDay
from tests.agent.conftest import extraction


def test_reads_a_well_formed_answer():
    parsed = parse_capture_extraction(extraction(payment="card"))
    assert parsed.kind is ExtractionKind.RECORD and parsed.amount == 5000
    assert parsed.direction is Direction.EXPENSE and parsed.payment_method is PaymentMethod.CARD
    assert parsed.when.day is SaidDay.TODAY and parsed.when.hour == 15


def test_unknown_becomes_none():
    parsed = parse_capture_extraction(extraction(direction="unknown", payment="unknown"))
    assert parsed.direction is None and parsed.payment_method is None


def test_minus_one_hour_means_not_said():
    parsed = parse_capture_extraction(extraction(hour=-1, minute=30))
    assert parsed.when.hour is None and parsed.when.minute == 0


def test_whole_float_is_an_integer():
    assert parse_capture_extraction(extraction(amount=5000.0)).amount == 5000


def test_merchant_is_trimmed_and_capped():
    parsed = parse_capture_extraction(extraction(merchant="  " + "가" * 60))
    assert parsed.merchant == "가" * 40


@pytest.mark.parametrize(
    "broken",
    [
        {"amount": "5000"},
        {"amount": 5000.5},
        {"amount": True},
        {"amount": -5000},
        {"kind": "transfer"},
        {"direction": "out"},
        {"merchant": None},
        {"hour": 25},
        {"day": "date", "month": 0},
        {"day": "next_week"},
    ],
)
def test_any_wrong_key_is_malformed(broken):
    with pytest.raises(MalformedOutput):
        parse_capture_extraction(extraction(**broken))


def test_missing_key_is_malformed():
    answer = extraction()
    del answer["amount"]
    with pytest.raises(MalformedOutput):
        parse_capture_extraction(answer)
