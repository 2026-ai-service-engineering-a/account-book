from __future__ import annotations

from agent.application.dto import Candidate
from agent.domain.values import CategoryId, Confidence


def test_carries_a_checked_confidence():
    assert Candidate(CategoryId("cafe"), Confidence(0.9)).confidence.value == 0.9
