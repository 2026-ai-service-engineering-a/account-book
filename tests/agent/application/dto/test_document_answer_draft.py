from __future__ import annotations

from agent.application.dto import DocumentAnswerDraft


def test_holds_what_the_model_said():
    draft = DocumentAnswerDraft("7일 안에 철회할 수 있어요.", ("c1",), False)
    assert draft.citations == ("c1",) and not draft.abstain
