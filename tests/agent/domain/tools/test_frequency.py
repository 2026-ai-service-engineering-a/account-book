from __future__ import annotations

from agent.domain.tools import Frequency


def test_nothing_counted_has_no_averages():
    empty = Frequency(0, 0, None, None)
    assert empty.avg_gap_days is None and empty.avg_amount is None
