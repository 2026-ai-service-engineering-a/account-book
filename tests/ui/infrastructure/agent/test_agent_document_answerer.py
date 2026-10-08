from __future__ import annotations

import asyncio
import json

import httpx

from tests.ui.infrastructure.agent.test_agent_document_gateway import CHUNK
from ui.application.dto import AnswerStatus
from ui.infrastructure.agent import AgentDocumentAnswerer
from ui.infrastructure.memory import MemoryDocumentGateway
from ui.infrastructure.scripted import ScriptedDocumentAnswerer


def answerer(handler) -> AgentDocumentAnswerer:
    fallback = ScriptedDocumentAnswerer(MemoryDocumentGateway())
    return AgentDocumentAnswerer(
        "http://agent", 1, fallback, transport=httpx.MockTransport(handler)
    )


def test_reads_the_cited_answer():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = {
            "status": "answered",
            "answer": "계약서를 받은 날부터 7일 안에 철회할 수 있어요.",
            "citations": [CHUNK],
            "chunks": [CHUNK],
            "reason": "",
            "mode": "hybrid",
            "fell_back": False,
        }
        return httpx.Response(200, json=body)

    answer = asyncio.run(answerer(handler).ask("노트북 취소"))
    assert json.loads(seen[0].content) == {"q": "노트북 취소"} and seen[0].url.path == "/ask"
    assert (
        answer.status is AnswerStatus.ANSWERED
        and answer.citations[0].title == "할부거래에 관한 법률"
    )


def test_a_dead_agent_falls_back_to_the_found_clauses_and_says_why():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    answer = asyncio.run(answerer(handler).ask("체력단련장"))
    assert answer.status is AnswerStatus.SEARCH_ONLY and answer.chunks
    assert "AI에 닿지 못해" in answer.reason
