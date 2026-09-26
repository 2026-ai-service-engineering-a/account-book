from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from ui.application.dto import ChatEvent
from ui.application.values import ProposalId


class ChatAgent(Protocol):
    """AI 자리 ① — 자연어 한 줄을 거래 제안이나 답으로 바꾼다.

    진짜는 `agent`의 `POST /chat` SSE다. 지금은 각본 대역이 선다.
    """

    def run(self, utterance: str) -> AsyncIterator[ChatEvent]: ...

    def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        """확인 카드의 답. 취소도 알린다 — 조용히 지우면 agent는 계속 기다린다."""
        ...
