from __future__ import annotations

from typing import Protocol

from ui.application.dto import DocumentAnswer


class DocumentAnswerer(Protocol):
    """AI 자리 — 법령 조문을 인용해 질문에 답한다(docs/ai/document-rag.md).

    진짜는 agent의 `POST /ask`다. 키 없이는 각본 대역이 찾은 조문만 보인다. 어떤 실패든 예외 대신
    찾은 조문만 보이는 답(search_only)으로 온다.
    """

    async def ask(self, question: str) -> DocumentAnswer: ...
