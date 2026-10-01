from __future__ import annotations

import pytest

from ui.application.values import CategoryId
from ui.infrastructure.memory.neighbor_vote import cosine, vote

CAFE, FOOD = CategoryId("cafe"), CategoryId("food")


def test_cosine():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine([0, 0], [1, 0]) == 0.0


def test_shares_sum_to_one_and_come_ranked():
    ranked = vote([(0.71, CAFE), (0.70, CAFE), (0.66, FOOD)], temperature=0.03)
    assert [c for c, _ in ranked] == [CAFE, FOOD]
    assert sum(p for _, p in ranked) == pytest.approx(1.0)


def test_closest_neighbour_outweighs_a_crowd():
    # 식비가 셋이어도 가장 비슷한 카페 하나가 이긴다 — 건수 투표가 아니다
    neighbors = [(0.72, CAFE), (0.65, FOOD), (0.65, FOOD), (0.65, FOOD)]
    assert vote(neighbors, temperature=0.03)[0][0] == CAFE


def test_high_temperature_is_almost_a_head_count():
    neighbors = [(0.72, CAFE), (0.65, FOOD), (0.65, FOOD), (0.65, FOOD)]
    assert vote(neighbors, temperature=10)[0][0] == FOOD


def test_no_neighbours_no_vote():
    assert vote([], temperature=0.03) == []
