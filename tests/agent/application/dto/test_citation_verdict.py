from __future__ import annotations

from agent.application.dto import CitationVerdict


def test_four_ends():
    assert [v.value for v in CitationVerdict] == ["ok", "unknown", "missing", "numbers"]
