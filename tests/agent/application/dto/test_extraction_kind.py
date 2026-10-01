from __future__ import annotations

from agent.application.dto import ExtractionKind


def test_only_record_fills_fields():
    assert [k.value for k in ExtractionKind] == ["record", "question", "cancellation", "unreadable"]
