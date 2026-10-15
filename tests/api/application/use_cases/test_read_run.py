from __future__ import annotations

import pytest

from api.application.use_cases import ReadRun
from api.domain.errors import RunNotFound
from tests.api.application.use_cases.test_decide_run import proposed


def test_reads_the_run_with_its_calls_and_age():
    found = ReadRun(proposed())("r1")
    assert found.tool_calls[0].tool == "create_transaction" and found.created_at is not None
    with pytest.raises(RunNotFound):
        ReadRun(proposed())("nope")
