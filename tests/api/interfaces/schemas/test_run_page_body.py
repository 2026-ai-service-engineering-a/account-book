from __future__ import annotations

from api.application.dto import RunPage, RunSummary
from api.domain.values import RunFlow, RunSeat
from api.interfaces.schemas import RunPageBody
from tests.api.application.dto.test_run_record import run_record


def test_a_line_carries_the_audit_columns_and_the_count():
    run = run_record("r1", seat=RunSeat.MCP, flow=RunFlow.DIRECT, utterance="", client="Claude")
    body = RunPageBody.of(RunPage((RunSummary(run, 2),), "next")).model_dump(mode="json")
    (line,) = body["items"]
    assert (line["seat"], line["flow"], line["client"], line["tool_count"]) == (
        "mcp",
        "direct",
        "Claude",
        2,
    )
    assert (line["model"], line["tokens"], line["cost_usd"]) == ("gemini/flash", 120, "0.000150")
    assert "tool_calls" not in line and body["next_cursor"] == "next"
