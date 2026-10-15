from __future__ import annotations

import pytest

from mcp_server.application.policies import RateLimit
from tests.mcp_server.conftest import Timer


def test_the_call_over_the_limit_waits_until_the_oldest_leaves_the_window():
    timer = Timer()
    limit = RateLimit(2, timer)
    assert limit.take() == 0
    timer.now = 20.0
    assert limit.take() == 0
    timer.now = 30.0
    assert limit.take() == 30  # 0초의 호출이 60초에 창을 떠난다
    timer.now = 60.0
    assert limit.take() == 0


def test_a_refused_call_is_not_counted():
    timer = Timer()
    limit = RateLimit(1, timer)
    assert limit.take() == 0
    for _ in range(5):
        assert limit.take() == 60
    timer.now = 60.0
    assert limit.take() == 0


def test_the_limit_is_at_least_one():
    with pytest.raises(ValueError):
        RateLimit(0, Timer())
