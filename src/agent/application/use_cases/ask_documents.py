from __future__ import annotations

import logging
from collections.abc import Mapping

from agent.application.dto import (
    AnswerStatus,
    DocumentAnswer,
    DocumentAnswerDraft,
    Retrieval,
    RetrievedChunk,
)
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.parsers import parse_document_answer
from agent.application.ports import LanguageModel
from agent.application.prompts import document_qa_prompt
from agent.domain.values import SearchMode

from .number_check import numbers_in, unsupported
from .retrieve import Retrieve

_log = logging.getLogger(__name__)


class AskDocuments:
    """문서 Q&A — 찾고, 인용하며 답하고, 검증한다(docs/ai/document-rag.md 4·5장). 단발 흐름이다.

    검색(기본 paragraph_item·hybrid·8) → 조각을 짧은 id·데이터 마커로 감싸 → complete_json 한 번.
    인용은 넘겨준 id 안에, 인용 없는 주장은 모른다고, 답의 숫자는 인용한 조각 안에. 어떤 실패든
    찾은 조각만 보이는 응답으로 떨어진다 — 예외를 위로 던지지 않는다(원칙 8).
    """

    def __init__(self, retrieve: Retrieve, model: LanguageModel) -> None:
        self._retrieve = retrieve
        self._model = model

    async def __call__(self, question: str) -> DocumentAnswer:
        try:
            retrieval = await self._retrieve(question)
        except LedgerUnavailable:
            empty = Retrieval(SearchMode.KEYWORD, True, ())
            return self._end(
                AnswerStatus.SEARCH_ONLY, empty, reason="지금은 문서를 찾을 수 없어요."
            )
        if not retrieval.chunks:
            return self._end(AnswerStatus.ABSTAINED, retrieval, reason="찾은 조문이 없어요.")
        labelled = {f"c{n}": chunk for n, chunk in enumerate(retrieval.chunks, start=1)}
        try:
            raw = await self._model.complete_json(
                document_qa_prompt(question, list(labelled.items()))
            )
            draft = parse_document_answer(raw)
        except (ModelUnavailable, MalformedOutput) as error:
            _log.warning("document answer failed: %s", type(error).__name__)
            return self._end(
                AnswerStatus.SEARCH_ONLY, retrieval, reason="지금은 답을 만들 수 없어요."
            )
        return self._checked(draft, labelled, retrieval)

    def _checked(
        self,
        draft: DocumentAnswerDraft,
        labelled: Mapping[str, RetrievedChunk],
        retrieval: Retrieval,
    ) -> DocumentAnswer:
        """5.3의 표. 걸리면 답을 버린다 — 고쳐서 내지 않는다."""
        if draft.abstain:
            return self._end(
                AnswerStatus.ABSTAINED, retrieval, reason="이 조문들에는 근거가 없어요."
            )
        if any(c not in labelled for c in draft.citations):
            return self._end(
                AnswerStatus.SEARCH_ONLY, retrieval, reason="답이 넘겨주지 않은 조문을 인용했어요."
            )
        if not draft.citations or not draft.answer:
            return self._end(
                AnswerStatus.ABSTAINED, retrieval, reason="근거를 인용하지 않은 답이라 버렸어요."
            )
        cited = tuple(labelled[c] for c in draft.citations)
        allowed = set().union(*(numbers_in(c.body) for c in cited))
        if unsupported(draft.answer, allowed):
            return self._end(
                AnswerStatus.SEARCH_ONLY, retrieval, reason="답의 숫자가 인용한 조문에 없어요."
            )
        return self._end(AnswerStatus.ANSWERED, retrieval, draft.answer, cited)

    def _end(
        self,
        status: AnswerStatus,
        retrieval: Retrieval,
        answer: str = "",
        cited: tuple[RetrievedChunk, ...] = (),
        reason: str = "",
    ) -> DocumentAnswer:
        # 운영 로그 — 끝과 개수만. 질문과 답은 남기지 않는다(development-rules 6.4)
        _log.info(
            "document answer status=%s chunks=%d citations=%d",
            status.value,
            len(retrieval.chunks),
            len(cited),
        )
        return DocumentAnswer(status, answer, cited, retrieval, reason)
