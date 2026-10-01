from __future__ import annotations

import pytest

from api.domain.rules.neighbor_vote import vote
from api.domain.values import CategoryId

CAFE, FOOD = CategoryId("cafe"), CategoryId("food")


def test_shares_sum_to_one_and_come_ranked():
    ranked = vote([(0.71, CAFE), (0.70, CAFE), (0.66, FOOD)], temperature=0.03)
    assert [c for c, _ in ranked] == [CAFE, FOOD]
    assert sum(p for _, p in ranked) == pytest.approx(1.0)


def test_closest_neighbour_outweighs_a_crowd():
    # 식비가 셋이어도 가장 비슷한 카페 하나가 이긴다 — 건수 투표가 아니다
    neighbors = [(0.72, CAFE), (0.65, FOOD), (0.65, FOOD), (0.65, FOOD)]
    assert vote(neighbors, temperature=0.03)[0][0] == CAFE
    assert vote(neighbors, temperature=10)[0][0] == FOOD  # 온도가 높으면 건수 투표에 가깝다


def test_no_neighbours_no_vote():
    assert vote([], temperature=0.03) == []
