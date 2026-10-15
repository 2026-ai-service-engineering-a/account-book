from __future__ import annotations

from agent.application.dto import InsightDraft


def test_an_empty_draft_is_a_draft():
    assert InsightDraft((), ()).charts == ()
