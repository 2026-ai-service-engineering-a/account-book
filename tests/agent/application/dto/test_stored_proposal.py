from __future__ import annotations

from datetime import UTC, datetime

from agent.application.dto import StoredProposal


def test_the_key_is_the_run_and_the_sequence():
    found = StoredProposal("r1", "awaiting_confirmation", datetime(2026, 10, 15, tzinfo=UTC),
                           "c2", {}, None)  # fmt: skip
    assert found.idempotency_key == "r1:2" and found.waiting
