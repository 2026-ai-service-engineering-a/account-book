from __future__ import annotations

from agent.application.dto import CategoryPick


def test_may_pick_nothing():
    pick = CategoryPick(None, (), "", abstain=True, self_confidence=0.2)
    assert pick.category_id is None and pick.abstain
