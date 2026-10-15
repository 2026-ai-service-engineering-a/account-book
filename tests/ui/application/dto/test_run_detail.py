from __future__ import annotations

from tests.ui.application.dto.test_run_line import line
from ui.application.dto import RunCall, RunDetail


def test_a_run_with_its_calls_in_order():
    calls = (RunCall("c1", "a", {}, None, None), RunCall("c2", "b", {}, None, None))
    assert [c.tool for c in RunDetail(line(), calls).calls] == ["a", "b"]
