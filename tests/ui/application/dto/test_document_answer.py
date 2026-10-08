from __future__ import annotations

from ui.application.dto import AnswerStatus, DocumentAnswer


def test_no_reason_unless_told():
    answer = DocumentAnswer(AnswerStatus.ANSWERED, "7일이에요.", (), ())
    assert answer.reason == ""
