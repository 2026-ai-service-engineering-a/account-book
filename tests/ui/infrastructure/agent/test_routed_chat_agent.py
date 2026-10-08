from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from ui.application.dto import ChatEvent
from ui.application.values import ProposalId
from ui.infrastructure.agent import RoutedChatAgent


class Side:
    def __init__(self, name: str) -> None:
        self.name = name
        self.heard: list[str] = []

    async def run(self, utterance: str) -> AsyncIterator[ChatEvent]:
        self.heard.append(utterance)
        yield ChatEvent("message", self.name)

    async def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        yield ChatEvent("message", f"{self.name} decided")


def first(stream: AsyncIterator[ChatEvent]) -> str:
    async def go() -> str:
        events = [e async for e in stream]
        return events[0].text

    return asyncio.run(go())


@pytest.mark.parametrize(
    ("utterance", "side"),
    [
        ("어제 점심 김밥천국 8500원 카드로", "records"),
        ("이마트 3만원 현금", "records"),
        ("저번 주에 카페 몇 번 갔어?", "questions"),
        ("이번 달 식비 얼마 썼어?", "questions"),
        ("5천원 넘게 쓴 거 보여줘", "questions"),  # 금액이 있어도 묻는 말이면 질문
        ("안녕", "questions"),
    ],
)
def test_code_decides_the_seat_not_the_model(utterance, side):
    chat = RoutedChatAgent(Side("questions"), Side("records"))
    assert first(chat.run(utterance)) == side


def test_confirmations_go_to_the_side_that_proposes():
    chat = RoutedChatAgent(Side("questions"), Side("records"))
    assert first(chat.decide(ProposalId("p1"), True)) == "records decided"
