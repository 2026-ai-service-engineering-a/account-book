from __future__ import annotations

import pytest

from agent.application.dto import ClassifyThresholds


def test_abstain_line_is_below_the_accept_line():
    with pytest.raises(ValueError):
        ClassifyThresholds(min_confidence=0.3, abstain_below=0.5)
    assert ClassifyThresholds(0.7, 0.25).min_confidence == 0.7
