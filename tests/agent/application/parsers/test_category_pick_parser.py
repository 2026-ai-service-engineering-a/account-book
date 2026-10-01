from __future__ import annotations

import pytest

from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_category_pick

ANSWER = {
    "category_id": "food",
    "evidence_ids": ["t3"],
    "reason": " 배달앱이라 식비로 봤어요. ",
    "abstain": False,
    "self_confidence": 0.8,
}


def test_reads_a_pick():
    pick = parse_category_pick(ANSWER)
    assert pick.category_id == "food" and pick.evidence_ids == ("t3",)
    assert pick.reason == "배달앱이라 식비로 봤어요."


def test_empty_category_is_none():
    assert parse_category_pick(ANSWER | {"category_id": ""}).category_id is None


@pytest.mark.parametrize(
    "broken",
    [
        {"category_id": None},
        {"evidence_ids": "t3"},
        {"evidence_ids": [3]},
        {"reason": 1},
        {"abstain": "false"},
        {"self_confidence": "high"},
        {"self_confidence": True},
    ],
)
def test_wrong_shape_is_malformed(broken):
    with pytest.raises(MalformedOutput):
        parse_category_pick(ANSWER | broken)
