from __future__ import annotations

import asyncio

from ui.application.dto import AnswerStatus
from ui.infrastructure.memory import MemoryDocumentGateway
from ui.infrastructure.scripted import ScriptedDocumentAnswerer


def test_shows_what_it_found_and_admits_it_is_a_stand_in():
    answer = asyncio.run(ScriptedDocumentAnswerer(MemoryDocumentGateway()).ask("체력단련장"))
    assert answer.status is AnswerStatus.SEARCH_ONLY and answer.answer == ""
    assert answer.chunks and "각본 대역" in answer.reason
