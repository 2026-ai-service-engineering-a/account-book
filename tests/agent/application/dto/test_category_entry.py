from __future__ import annotations

from agent.application.dto import CategoryEntry
from agent.domain.values import CategoryId


def test_id_and_name():
    assert CategoryEntry(CategoryId("cafe"), "카페").name == "카페"
