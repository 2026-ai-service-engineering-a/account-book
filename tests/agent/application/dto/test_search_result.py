from __future__ import annotations

from tests.agent.conftest import search


def test_name_of_falls_back_to_the_id():
    result = search()
    assert result.name_of("cafe") == "카페" and result.name_of("unknown") == "unknown"
