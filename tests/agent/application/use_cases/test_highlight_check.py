from __future__ import annotations

from datetime import date

from agent.application.dto import HighlightDraft, ToolCall, ToolResult, ToolStep
from agent.application.use_cases.highlight_check import SCOLDING, kept_highlights

END = date(2026, 9, 30)
STEP = ToolStep(
    ToolCall("call_1", "summarize_spending", {}),
    ToolResult("call_1", data={"expense": {"amount": 1462000, "currency": "KRW"}}),
)


def test_numbers_are_checked_like_the_chat_answer():
    drafts = [
        HighlightDraft("9월에 1,462,000원 썼어요.", ""),
        HighlightDraft("하루 48,733원꼴이에요.", ""),
    ]
    assert kept_highlights(drafts, [STEP], date(2026, 9, 30)) == ("9월에 1,462,000원 썼어요.",)


def test_every_scolding_word_drops_the_sentence():
    for word in SCOLDING:
        assert (
            kept_highlights([HighlightDraft(f"식비를 {word}", "")], [STEP], date(2026, 9, 30)) == ()
        )
