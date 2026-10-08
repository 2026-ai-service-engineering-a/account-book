from __future__ import annotations

import pytest

from api.domain.rules.rank_fusion import RRF_CONSTANT, reciprocal_rank_fusion


def test_sums_reciprocal_ranks_not_scores():
    fused = dict(reciprocal_rank_fusion([["a", "b", "c"], ["c", "a"]]))
    assert fused["a"] == pytest.approx(1 / (RRF_CONSTANT + 1) + 1 / (RRF_CONSTANT + 2))
    assert fused["b"] == pytest.approx(1 / (RRF_CONSTANT + 2))


def test_both_lists_agreeing_beats_one_list_shouting():
    order = [key for key, _ in reciprocal_rank_fusion([["x", "both"], ["y", "both"]])]
    assert order[0] == "both"


def test_ties_go_to_the_higher_rank_anywhere():
    # a는 첫 목록 1위, b는 둘째 목록 1위 — 점수가 같으면 식별자 순
    assert [k for k, _ in reciprocal_rank_fusion([["a"], ["b"]])] == ["a", "b"]
    assert reciprocal_rank_fusion([[], []]) == []
