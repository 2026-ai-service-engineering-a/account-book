from __future__ import annotations

import asyncio
import dataclasses
from datetime import date

import pytest

from agent.application.dto import AnswerStatus, DocumentAnswer, RetrievedChunk
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.use_cases import AskDocuments, Retrieve
from agent.domain.values import ChunkStrategy
from tests.agent.conftest import FakeLedger, FakeModel

WITHDRAW = RetrievedChunk(
    "paragraph_item:할부거래에 관한 법률/제8조/1/1",
    "할부거래에 관한 법률",
    date(2026, 9, 8),
    ChunkStrategy.PARAGRAPH_ITEM,
    "제8조(청약의 철회) ① 1.",
    "- 1. 제6조제1항에 따른 계약서를 받은 날부터 7일.",
    0.03,
)
TRANSIT = dataclasses.replace(
    WITHDRAW,
    id="paragraph_item:조세특례제한법/제126조의2/2/2",
    title="조세특례제한법",
    heading="제126조의2(신용카드 등 사용금액에 대한 소득공제) ② 2.",
    body="- 2. … 대중교통이용분 \N{MULTIPLICATION SIGN} 100분의 40",
)


def reply(
    answer: str = "", citations: tuple[str, ...] = (), abstain: bool = False
) -> dict[str, object]:
    return {"answer": answer, "citations": list(citations), "abstain": abstain}


def ask(*replies: object, chunks: object = (WITHDRAW, TRANSIT)) -> tuple[DocumentAnswer, FakeModel]:
    model = FakeModel(*replies)  # type: ignore[arg-type]  # 예외도 섞어 넣는다
    ledger = FakeLedger(replies={"search_documents": chunks})
    answer = asyncio.run(
        AskDocuments(Retrieve(ledger, None, None), model)("노트북 며칠 안에 취소?")
    )
    return answer, model


def test_a_cited_answer_with_numbers_from_the_cited_text():
    answer, model = ask(reply("계약서를 받은 날부터 7일 안에 철회할 수 있어요.", ("c1",)))
    assert answer.status is AnswerStatus.ANSWERED
    assert answer.citations == (WITHDRAW,) and answer.chunks == (WITHDRAW, TRANSIT)
    assert len(model.prompts) == 1 and "[c2] 조세특례제한법" in model.prompts[0].user


def test_one_hundred_parts_of_forty_is_forty_percent():
    answer, _ = ask(reply("버스·지하철은 40%를 공제해요.", ("c2",)))
    assert answer.status is AnswerStatus.ANSWERED


@pytest.mark.parametrize(
    ("draft", "status"),
    [
        (reply(abstain=True), AnswerStatus.ABSTAINED),
        (reply("7일이에요.", ("c9",)), AnswerStatus.SEARCH_ONLY),  # 넘겨주지 않은 id
        (reply("7일이에요."), AnswerStatus.ABSTAINED),  # 인용 없는 주장
        (
            reply("30일 안에 철회할 수 있어요.", ("c1",)),
            AnswerStatus.SEARCH_ONLY,
        ),  # 인용에 없는 숫자
        (reply("40%예요.", ("c1",)), AnswerStatus.SEARCH_ONLY),  # 숫자가 다른 조각의 것
    ],
)
def test_what_does_not_pass_is_dropped_not_fixed(draft, status):
    answer, _ = ask(draft)
    assert answer.status is status and answer.answer == "" and answer.citations == ()
    assert answer.chunks == (WITHDRAW, TRANSIT) and answer.reason


@pytest.mark.parametrize("failure", [ModelUnavailable("down"), MalformedOutput("x"), {"answer": 1}])
def test_any_generation_failure_falls_back_to_the_search_results(failure):
    answer, model = ask(failure)
    assert answer.status is AnswerStatus.SEARCH_ONLY and answer.chunks == (WITHDRAW, TRANSIT)
    assert len(model.prompts) == 1  # 다시 시키지 않는다 — 한 번이다


def test_nothing_found_is_abstain_without_calling_the_model():
    answer, model = ask(chunks=())
    assert answer.status is AnswerStatus.ABSTAINED and model.prompts == []


def test_search_down_is_search_only_with_nothing_to_show():
    answer, model = ask(chunks=LedgerUnavailable("ConnectError"))
    assert (answer.status, answer.chunks, model.prompts) == (AnswerStatus.SEARCH_ONLY, (), [])
