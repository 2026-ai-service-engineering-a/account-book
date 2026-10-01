from __future__ import annotations

import pytest
from pydantic import ValidationError

from ui.infrastructure.agent import AgentCaptureReply

BODY = {
    "direction": None,
    "amount": None,
    "occurred_at": None,
    "payment_method": None,
    "merchant": None,
    "refusal": "못 읽었어요",
}


def test_accepts_a_refusal():
    assert AgentCaptureReply.model_validate(BODY).refusal == "못 읽었어요"


@pytest.mark.parametrize("broken", [{"amount": 0}, {"direction": "out"}, {"payment_method": "x"}])
def test_rejects_values_the_ui_does_not_know(broken):
    with pytest.raises(ValidationError):
        AgentCaptureReply.model_validate(BODY | broken)
