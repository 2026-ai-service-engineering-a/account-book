from __future__ import annotations

import asyncio
import logging

import pytest

from agent.application.dto import RunRecord, RunSeat
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.application.use_cases import RecordRun
from tests.agent.conftest import FakeRecorder

RUN = RunRecord("r-1", RunSeat.CAPTURE, "블루보틀 성수 12,345원", "read")


def test_passes_the_run_with_the_model_name():
    recorder = FakeRecorder()
    asyncio.run(RecordRun(recorder, "gemini/flash")(RUN))
    assert recorder.runs == [(RUN, "gemini/flash")]


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (
            LedgerRejected(422, "validation_error", {"utterance": "블루보틀 성수"}),
            "validation_error",
        ),
        (LedgerUnavailable("ConnectError"), "unavailable"),
        (RuntimeError("블루보틀 성수 12,345원"), "RuntimeError"),
    ],
)
def test_a_failure_is_swallowed_and_logged_with_the_run_id_and_code_only(failure, code, caplog):
    caplog.set_level(logging.DEBUG, logger="agent")
    asyncio.run(RecordRun(FakeRecorder(fail=failure), "m")(RUN))  # 던지지 않는다
    (line,) = [r.getMessage() for r in caplog.records if r.name.startswith("agent")]
    assert line == f"run record failed run_id=r-1 code={code}"
