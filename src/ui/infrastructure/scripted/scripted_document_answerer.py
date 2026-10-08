from __future__ import annotations

from ui.application.dto import AnswerStatus, ChunkStrategy, DocumentAnswer
from ui.application.ports import DocumentGateway

_STAND_IN = "각본 대역이라 답 문장은 만들지 않아요. 찾은 조문을 펼쳐 보세요."


class ScriptedDocumentAnswerer:
    """문서 Q&A의 각본 대역 — 낱말로 찾은 조문만 보인다. 답 문장을 흉내 내지 않는다.

    대역이 그럴듯한 문장을 만들기 시작하면 진짜로 바꿀 때 무엇이 달라졌는지 가려진다(stand-ins.md).
    """

    def __init__(self, documents: DocumentGateway) -> None:
        self._documents = documents

    async def ask(self, question: str) -> DocumentAnswer:
        found = await self._documents.search(question, ChunkStrategy.PARAGRAPH_ITEM)
        return DocumentAnswer(AnswerStatus.SEARCH_ONLY, "", (), found.hits, _STAND_IN)
