from __future__ import annotations

from collections.abc import AsyncIterator

from ui.application.dto import ChatEvent
from ui.application.ports import ChatAgent
from ui.application.values import ProposalId
from ui.infrastructure.scripted.utterance_parser import UtteranceParser


class RoutedChatAgent:
    """채팅 입력창 하나에 기록과 질문이 같이 들어온다. 어느 쪽인지는 코드가 정한다.

    금액이 있고 질문 낱말이 없으면 기록 — 기록 쪽(지금은 각본 대역)으로. 그 밖은 질문 —
    agent의 query 모드로. 모델이 모드를 고르게 하지 않는다(docs/ai/tools.md 6장).
    확인 카드는 기록 쪽만 내므로 확인은 언제나 기록 쪽으로 간다.
    """

    def __init__(self, questions: ChatAgent, records: ChatAgent) -> None:
        self._questions = questions
        self._records = records
        self._parser = UtteranceParser()

    def run(self, utterance: str) -> AsyncIterator[ChatEvent]:
        parsed = self._parser.parse(utterance)
        is_record = parsed.amount is not None and not parsed.is_question
        return (self._records if is_record else self._questions).run(utterance)

    def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        return self._records.decide(proposal_id, accepted)
