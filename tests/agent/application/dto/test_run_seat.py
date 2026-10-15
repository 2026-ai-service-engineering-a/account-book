from __future__ import annotations

from agent.application.dto import RunSeat


def test_same_values_as_the_api_check():
    assert {s.value for s in RunSeat} == {"capture", "classify", "chat", "ask", "insight"}


def test_each_seat_has_its_flow():
    # 채팅은 ReAct, 리포트는 plan-and-execute, 나머지는 단발(ai/agent-loop.md 3장)
    assert {s: s.flow for s in RunSeat} == {
        RunSeat.CAPTURE: "single",
        RunSeat.CLASSIFY: "single",
        RunSeat.CHAT: "react",
        RunSeat.ASK: "single",
        RunSeat.INSIGHT: "plan_execute",
    }
