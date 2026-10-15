from __future__ import annotations

from agent.application.dto import ExtractionKind


def test_only_record_fills_fields():
    assert [k.value for k in ExtractionKind] == [
        "record",
        "question",
        "cancellation",
        "planned",  # 아직 쓰지 않은 돈 — 평가에서 "내일 회식 3만원 예정"이 오늘 기록이 됐다
        "unreadable",
    ]
