from __future__ import annotations

from api.application.dto import RunSummary
from tests.api.application.dto.test_run_record import run_record


def test_carries_the_count_not_the_calls():
    line = RunSummary(run_record(), 3)
    assert line.run.tool_calls == () and line.tool_count == 3
