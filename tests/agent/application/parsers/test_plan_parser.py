from __future__ import annotations

import pytest

from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_plan


def test_arguments_come_as_json_text():
    (step,) = parse_plan(
        {"steps": [{"tool": "detect_outliers", "args": '{"period": "this_month"}', "why": "큰 건"}]}
    )
    assert (step.tool, step.arguments, step.why) == (
        "detect_outliers",
        {"period": "this_month"},
        "큰 건",
    )


@pytest.mark.parametrize("args", ["{not json", "[1, 2]", '"this_month"'])
def test_arguments_that_are_not_an_object_leave_the_step_for_the_check_to_drop(args):
    (step,) = parse_plan({"steps": [{"tool": "t", "args": args, "why": ""}]})
    assert step.arguments is None


@pytest.mark.parametrize(
    "raw", [{}, {"steps": "no"}, {"steps": [1]}, {"steps": [{"tool": "t", "args": {}, "why": ""}]}]
)
def test_a_wrong_shape_is_malformed(raw):
    with pytest.raises(MalformedOutput):
        parse_plan(raw)


def test_an_empty_plan_is_a_plan():
    assert parse_plan({"steps": []}) == ()
