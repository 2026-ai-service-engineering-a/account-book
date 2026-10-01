from __future__ import annotations

from tests.api.conftest import draft


def test_memo_defaults_to_empty():
    assert draft().memo == ""
