"""LLM이 낸 JSON을 `DocumentAnswerDraft`로. `Any`(모양을 모르는 값)는 여기서 끝난다."""

from __future__ import annotations

from collections.abc import Mapping

from agent.application.dto import DocumentAnswerDraft
from agent.application.errors import MalformedOutput

_ANSWER_LIMIT = 1_000  # 한두 문장을 시켰다. 이보다 길면 조문을 통째로 옮긴 것이다


def parse_document_answer(raw: Mapping[str, object]) -> DocumentAnswerDraft:
    """모양이 틀리면 `MalformedOutput` — 부르는 쪽이 검색 결과만 보이는 응답으로 떨어진다."""
    answer, citations, abstain = raw.get("answer"), raw.get("citations"), raw.get("abstain")
    if not isinstance(answer, str):
        raise MalformedOutput("answer가 글이 아니다")
    if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
        raise MalformedOutput("citations가 글의 목록이 아니다")
    if not isinstance(abstain, bool):
        raise MalformedOutput("abstain이 참거짓이 아니다")
    if len(answer) > _ANSWER_LIMIT:
        raise MalformedOutput("answer가 너무 길다")
    unique = tuple(dict.fromkeys(c.strip() for c in citations if c.strip()))
    return DocumentAnswerDraft(answer=answer.strip(), citations=unique, abstain=abstain)
