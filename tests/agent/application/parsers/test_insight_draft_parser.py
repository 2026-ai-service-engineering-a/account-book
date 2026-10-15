from __future__ import annotations

import pytest

from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_insight_draft
from tests.agent.application.use_cases.test_build_insights import assembled, chart


def test_reads_charts_and_sentences():
    draft = parse_insight_draft(assembled([chart()], "식비는 412,000원이었어요."))
    (spec,) = draft.charts
    assert (spec.kind, spec.source, spec.annotate, spec.carried_values) == (
        "hbar",
        "call_2",
        ("생활",),
        False,
    )
    assert draft.highlights[0].text == "식비는 412,000원이었어요."


def test_values_riding_on_a_spec_are_marked_not_refused():
    # 버리는 것은 검사의 일이다 — 한 차트 때문에 전체를 다시 시키지 않는다
    draft = parse_insight_draft(assembled([chart() | {"values": [1, 2]}]))
    assert draft.charts[0].carried_values


@pytest.mark.parametrize(
    "raw",
    [{"charts": []}, {"charts": [1], "highlights": []}, assembled([chart(title=3)])],
)
def test_a_wrong_shape_is_malformed(raw):
    with pytest.raises(MalformedOutput):
        parse_insight_draft(raw)
