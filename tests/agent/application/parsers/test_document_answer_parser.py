from __future__ import annotations

import pytest

from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_document_answer


def test_reads_and_tidies_the_answer():
    draft = parse_document_answer(
        {"answer": " 7일이에요. ", "citations": ["c2", " c2 ", "", "c1"], "abstain": False}
    )
    assert (draft.answer, draft.citations, draft.abstain) == ("7일이에요.", ("c2", "c1"), False)


@pytest.mark.parametrize(
    "raw",
    [
        {"answer": 7, "citations": [], "abstain": False},
        {"answer": "x", "citations": "c1", "abstain": False},
        {"answer": "x", "citations": [1], "abstain": False},
        {"answer": "x", "citations": [], "abstain": "no"},
        {"answer": "가" * 1001, "citations": [], "abstain": False},
    ],
)
def test_wrong_shapes_are_malformed(raw):
    with pytest.raises(MalformedOutput):
        parse_document_answer(raw)
