from __future__ import annotations

import asyncio

import pytest

from tests.ui.conftest import draft, key
from ui.application.dto import Source
from ui.application.values import CategoryId, Money
from ui.infrastructure.memory import (
    MemoryBudgetGateway,
    MemoryCatalogGateway,
    MemoryReportGateway,
    MemoryTransactionGateway,
)
from ui.infrastructure.scripted import ScriptedCategorySuggester, ScriptedChatAgent


@pytest.fixture
def agent(store, clock):
    return ScriptedChatAgent(
        MemoryTransactionGateway(store),
        MemoryReportGateway(store, clock),
        MemoryBudgetGateway(store, clock),
        MemoryCatalogGateway(store),
        ScriptedCategorySuggester(),
        clock,
        token_delay=0,
    )


def collect(stream):
    async def go():
        return [event async for event in stream]

    return asyncio.run(go())


def test_record_needs_confirmation(agent, store):
    events = collect(agent.run("어제 점심 김밥천국 8500원 카드로"))
    kinds = [e.kind for e in events]
    assert kinds == ["tool", "tool", "proposal", "done"]
    proposal = events[2].proposal
    assert (proposal.category_name, proposal.amount, str(proposal.occurred_on)) == (
        "식비",
        Money(8_500),
        "2026-09-16",
    )
    assert store.transactions == {}  # 확인 전에는 아무것도 쓰지 않는다

    result = collect(agent.decide(proposal.id, accepted=True))
    assert result[-2].kind == "message" and result[-2].text.startswith("기록했어요.")
    (saved,) = store.transactions.values()
    assert saved.source == Source.AGENT


def test_cancel_writes_nothing_and_cannot_replay(agent, store):
    proposal = collect(agent.run("스타벅스 5800원"))[2].proposal
    assert collect(agent.decide(proposal.id, accepted=False))[-2].text.startswith("취소")
    assert store.transactions == {}
    assert collect(agent.decide(proposal.id, accepted=True))[0].code == "not_found"


def test_budget_line_after_record(agent, store):
    store.limits[CategoryId("food")] = Money(300_000)
    asyncio.run(MemoryTransactionGateway(store).create(draft(amount=173_800, day=2), key("k")))
    proposal = collect(agent.run("어제 점심 김밥천국 8500원"))[2].proposal
    text = collect(agent.decide(proposal.id, accepted=True))[-2].text
    assert "9월 식비 182,300원 / 예산 300,000원 (60%)." in text
    assert "9월 28일에 예산을 넘고" in text


def test_question_is_answered_from_report(agent, store):
    asyncio.run(
        MemoryTransactionGateway(store).create(draft(amount=31_000, category="cafe"), key("k"))
    )
    events = collect(agent.run("이번 달 카페에 얼마 썼어?"))
    assert events[0].text == "summarize_spending"
    assert events[-2].text == "이번 달(9/1~9/17) 카페에 31,000원 썼어요."
    assert "".join(e.text for e in events if e.kind == "token") == events[-2].text


def test_unknown_sentence_admits_it_is_scripted(agent):
    events = collect(agent.run("안녕"))
    assert "각본 대역" in events[-2].text


def test_last_month_names_its_whole_range(agent):
    events = collect(agent.run("지난달 얼마 썼어?"))
    assert events[-2].text.startswith("지난달(8/1~8/31) 지출은")


@pytest.mark.parametrize("question", ["8월 식비는?", "지지난 달 식비 얼마?", "저번 주 카페 얼마?"])
def test_periods_it_cannot_read_are_admitted_not_guessed(agent, question):
    events = collect(agent.run(question))
    # 집계를 부르지 않는다 — tool 이벤트가 없다
    assert [e.kind for e in events if e.kind != "token"] == ["message", "done"]
    assert "이번 달과 지난달만" in events[-2].text


def test_last_month_compares_with_the_month_before_it(agent, store):
    gateway = MemoryTransactionGateway(store)
    asyncio.run(gateway.create(draft(amount=5_000, month=7), key("july")))
    asyncio.run(gateway.create(draft(amount=9_000, month=8), key("august")))
    text = collect(agent.run("지난달 식비 얼마 썼어?"))[-2].text
    # "지난달(8월) … 지난달보다"가 아니다 — 견주는 건 그 전 달(7월)이다
    assert text == "지난달(8/1~8/31) 식비에 9,000원 썼어요. 그 전 달보다 4,000원 많습니다."
