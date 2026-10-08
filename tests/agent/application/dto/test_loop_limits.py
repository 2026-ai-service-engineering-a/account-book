from __future__ import annotations

import pytest

from agent.application.dto import LoopLimits


@pytest.mark.parametrize(("steps", "cost", "wall"), [(0, 0.5, 20), (8, 0, 20), (8, 0.5, 0)])
def test_limits_must_be_positive(steps, cost, wall):
    with pytest.raises(ValueError):
        LoopLimits(steps, cost, wall)
