from __future__ import annotations

from datetime import datetime

import pytest

from agent.domain.values import CaptureReading, Money


def test_refused_leaves_every_field_empty():
    reading = CaptureReading.refused("못 읽었어요")
    fields = (reading.direction, reading.amount, reading.occurred_at, reading.payment_method)
    assert fields == (None, None, None, None) and reading.merchant is None


def test_cannot_refuse_and_fill_at_once():
    with pytest.raises(ValueError):
        CaptureReading(amount=Money(5000), refusal="못 읽었어요")


def test_time_must_be_aware():
    with pytest.raises(ValueError):
        CaptureReading(amount=Money(5000), occurred_at=datetime(2026, 10, 1, 15))


def test_category_is_absent_unless_chosen():
    assert CaptureReading(amount=Money(5000)).category is None
