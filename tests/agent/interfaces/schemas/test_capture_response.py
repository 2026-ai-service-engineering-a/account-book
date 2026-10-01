from __future__ import annotations

from datetime import datetime

from agent.domain.values import CaptureReading, Direction, Money, PaymentMethod
from agent.interfaces.schemas import CaptureResponse
from tests.agent.conftest import SEOUL


def test_plain_values_on_the_wire():
    reading = CaptureReading(
        direction=Direction.EXPENSE,
        amount=Money(8500),
        occurred_at=datetime(2026, 9, 16, 12, 31, tzinfo=SEOUL),
        payment_method=PaymentMethod.CARD,
        merchant="김밥천국",
    )
    body = CaptureResponse.of(reading).model_dump(mode="json")
    assert body == {
        "direction": "expense",
        "amount": 8500,
        "occurred_at": "2026-09-16T12:31:00+09:00",
        "payment_method": "card",
        "merchant": "김밥천국",
        "refusal": "",
    }


def test_refusal_is_all_nulls():
    body = CaptureResponse.of(CaptureReading.refused("못 읽었어요")).model_dump()
    assert body["refusal"] == "못 읽었어요" and body["amount"] is None
