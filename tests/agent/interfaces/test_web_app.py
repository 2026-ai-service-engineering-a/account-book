from __future__ import annotations

import logging

import pytest

from agent.application.dto import ModelReply, ModelUsage, ToolCall
from agent.application.errors import LedgerRejected, ModelUnavailable
from agent.domain.tools import CategoryLine, Frequency
from agent.domain.values import Amount, CategoryId
from tests.agent.application.use_cases.test_ask_documents import TRANSIT, WITHDRAW, reply
from tests.agent.conftest import FakeLedger, FakeModel, FakeRecorder, extraction, search
from tests.agent.interfaces.conftest import client_with

# 운영 로그에 나오면 안 되는 것 — 발화·금액·가맹점(development-rules 6.4)
MERCHANT = "블루보틀 성수"
SAID = f"{MERCHANT}에서 12,345원 썼어"
SENTINELS = ("블루보틀", "성수", "12345", "12,345", "비밀메모")
NOW = {"now": "2026-10-08T09:00:00+09:00", "timezone": "Asia/Seoul"}
# LogRecord가 원래 갖는 칸. 나머지가 extra로 실린 값이다
_STANDARD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def test_headless_no_docs_pages():
    client = client_with(FakeModel())
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def _logged(record: logging.LogRecord) -> list[str]:
    extras = [str(v) for k, v in record.__dict__.items() if k not in _STANDARD]
    return [record.getMessage(), *extras]


def _every_seat_with_a_failing_recorder() -> None:
    """네 자리와 503 길을 한 번씩. 기록은 매번 실패하고, 실패에는 보낸 값이 섞여 돌아온다."""
    refused = LedgerRejected(422, "validation_error", {"utterance": SAID})
    leaky = RuntimeError(SAID)
    cafe = FakeLedger(search(candidates=(("cafe", 0.9),)))
    said = extraction(amount=12345, merchant=MERCHANT)
    client_with(FakeModel(said), cafe, FakeRecorder(fail=refused)).post(
        "/capture", json={"text": SAID, **NOW}
    )
    client_with(FakeModel(ModelUnavailable("x")), recorder=FakeRecorder(fail=leaky)).post(
        "/capture", json={"text": SAID, **NOW}
    )
    client_with(
        FakeModel(), FakeLedger(search(candidates=(("cafe", 0.9),))), FakeRecorder(fail=leaky)
    ).post("/classify", json={"merchant": MERCHANT, "memo": "비밀메모", "direction": "expense"})
    arguments = {"period": "last_week", "merchant": MERCHANT}
    model = FakeModel(
        tape=[
            ModelReply("", (ToolCall("c1", "count_frequency", arguments),), ModelUsage(9, 1)),
            ModelReply(f"{MERCHANT}에 3번, 12,345원 썼어요.", (), ModelUsage(9, 1)),
        ]
    )
    chat_ledger = FakeLedger(
        replies={
            "categories": (CategoryLine(CategoryId("cafe"), "카페"),),
            "frequency": Frequency(3, 3, 1.0, Amount(12345)),
        }
    )
    client_with(model, chat_ledger, FakeRecorder(fail=refused)).post(
        "/chat", json={"text": f"{MERCHANT} 몇 번 갔어?", **NOW}
    )
    documents = FakeLedger(replies={"search_documents": (WITHDRAW, TRANSIT)})
    client_with(FakeModel(reply("7일", ("c1",))), documents, FakeRecorder(fail=leaky)).post(
        "/ask", json={"q": f"{MERCHANT} 12,345원 환불"}
    )


def test_operation_logs_never_carry_the_utterance_amount_or_merchant(caplog):
    caplog.set_level(logging.DEBUG)
    _every_seat_with_a_failing_recorder()
    lines = [text for record in caplog.records for text in _logged(record)]
    # 다섯 번 다 기록에 실패했고, 그 사실은 run_id와 코드로만 남았다
    failures = [line for line in lines if line.startswith("run record failed")]
    assert len(failures) == 5 and all("run_id=" in line for line in failures)
    leaked = [(s, line) for line in lines for s in SENTINELS if s in line]
    assert leaked == []


@pytest.mark.parametrize("sentinel", ["블루보틀", "12,345", "비밀메모"])
def test_the_audit_record_does_keep_them(sentinel):
    # 반대쪽 확인 — 감사 테이블로 가는 기록에는 남는다. 안 남기는 게 아니라 자리가 다르다.
    # 기록(capture)이 읽어 낸 값은 따로 싣지 않는다 — 원문 발화가 남는다
    recorder = FakeRecorder()
    said = extraction(amount=12345, merchant=MERCHANT)
    cafe = FakeLedger(search(candidates=(("cafe", 0.9),)))
    client_with(FakeModel(said), cafe, recorder).post("/capture", json={"text": SAID, **NOW})
    client_with(FakeModel(), FakeLedger(search()), recorder).post(
        "/classify", json={"merchant": MERCHANT, "memo": "비밀메모", "direction": "expense"}
    )
    kept = " ".join(f"{run.utterance} {run.tool_calls}" for run, _ in recorder.runs)
    assert sentinel in kept
