from __future__ import annotations

from agent.application.dto import CaptureExtraction, ExtractionKind
from agent.domain.values import SaidWhen


def test_carries_the_said_form_not_a_date():
    extraction = CaptureExtraction(
        kind=ExtractionKind.RECORD,
        amount=5000,
        direction=None,
        payment_method=None,
        merchant="카페",
        when=SaidWhen(hour=15),
    )
    assert extraction.when.hour == 15 and not hasattr(extraction, "occurred_at")
