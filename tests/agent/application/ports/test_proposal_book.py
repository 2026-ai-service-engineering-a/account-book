from __future__ import annotations

import inspect

from agent.application.ports import ProposalBook, RunRecorder
from agent.infrastructure.http import HttpProposalBook
from tests.agent.fake_audit import FakeAuditTable


def test_adapter_and_fake_fill_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    real: ProposalBook = HttpProposalBook("http://api:8000", timeout=1)
    fake: ProposalBook = FakeAuditTable()
    recorder: RunRecorder = FakeAuditTable()  # 같은 가짜가 제안을 남기는 쪽도 한다
    assert inspect.iscoroutinefunction(real.confirm) and inspect.iscoroutinefunction(fake.close)
    assert inspect.iscoroutinefunction(recorder.record)
