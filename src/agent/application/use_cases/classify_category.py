from __future__ import annotations

import dataclasses
import logging
import re

from agent.application.dto import (
    CategoryPick,
    CategoryQuery,
    ClassifyThresholds,
    SearchResult,
    SearchStrategy,
)
from agent.application.errors import MalformedOutput, ModelUnavailable
from agent.application.parsers import parse_category_pick
from agent.application.ports import Embedder, LanguageModel, LedgerApi
from agent.application.prompts import classify_prompt
from agent.domain.values import CategoryChoice, ChoiceStrategy, Direction

from .sync_index import SyncIndex

_ATTEMPTS = 2
_REASON_LIMIT = 80
# 근거 줄에 이름을 몇 개까지 보이나
_SHOWN = 3
# reason에 이런 말이 섞였으면 지시문이 샌 것이다. reason만 버리고 카테고리는 쓴다(7장)
_LEAKED = re.compile(r"<<<|>>>|DATA|지시|무시|프롬프트|system", re.IGNORECASE)
_FIRST_SENTENCE = re.compile(r"(?<=[.!?])\s+")

NO_INPUT = "가맹점이나 메모를 넣으면 골라 드려요."
NO_EVIDENCE = "고를 만한 근거가 없어요. 직접 골라 주세요."
AI_PICKED = "비슷한 기록을 보고 AI가 골랐어요."

_log = logging.getLogger(__name__)


class ClassifyCategory:
    """카테고리 고르기 — RAG(docs/ai/category-suggestion-rag.md). 단발, LLM 0~1회.

    검색은 api가 한다(규칙 → 이력 → 벡터 이웃). 여기서는 검색이 낸 신뢰도로 갈림길만 정하고,
    애매할 때만 LLM에게 후보와 근거를 보여 준다. LLM이 정하는 것은 "후보 중 어느 것, 아니면
    모르겠다" 하나뿐이다.
    """

    def __init__(
        self,
        ledger: LedgerApi,
        model: LanguageModel,
        thresholds: ClassifyThresholds,
        embedder: Embedder | None = None,
    ) -> None:
        self._ledger = ledger
        self._model = model
        self._thresholds = thresholds
        self._embedder = embedder
        self._index = SyncIndex(ledger, embedder) if embedder else None

    async def __call__(self, merchant: str, memo: str, direction: Direction) -> CategoryChoice:
        """api에 닿지 못하면 `LedgerUnavailable`, LLM에 닿지 못하면 `ModelUnavailable`."""
        if not (merchant.strip() or memo.strip()):
            return CategoryChoice.abstain(NO_INPUT)
        result = await self._search(CategoryQuery(merchant, memo, direction))
        return await self._decide(result, merchant, memo, direction)

    async def _search(self, query: CategoryQuery) -> SearchResult:
        if self._embedder is None or self._index is None:
            return await self._ledger.suggest(query)
        query = dataclasses.replace(query, embedding_model=self._embedder.model)
        try:
            await self._index.run()
        except ModelUnavailable:
            # 색인이 늦는 것은 품질 문제이고 장애가 아니다(4.3). 있는 벡터로 계속한다.
            _log.warning("embedding sync skipped")
        result = await self._ledger.suggest(query)
        if not result.needs_query_vector:
            return result
        try:
            (vector,) = await self._embedder.embed([result.query_text])
        except ModelUnavailable:
            _log.warning("query embedding skipped")
            return result
        return await self._ledger.suggest(dataclasses.replace(query, query_vector=vector))

    async def _decide(
        self, result: SearchResult, merchant: str, memo: str, direction: Direction
    ) -> CategoryChoice:
        if not result.candidates:
            return CategoryChoice.abstain(NO_EVIDENCE)
        top = result.candidates[0]
        name = result.name_of(top.category_id)
        if result.strategy is SearchStrategy.RULE:
            return CategoryChoice(top.category_id, ChoiceStrategy.RULE, f"직접 만든 규칙: {name}")
        if result.strategy is SearchStrategy.HISTORY:
            agree = sum(e.category_id == top.category_id for e in result.evidence)
            reason = f"같은 가맹점 최근 {len(result.evidence)}건 중 {agree}건: {name}"
            return CategoryChoice(top.category_id, ChoiceStrategy.HISTORY, reason)
        confidence = top.confidence.value
        if confidence >= self._thresholds.min_confidence:
            return CategoryChoice(top.category_id, ChoiceStrategy.VECTOR, _similar(result))
        if confidence < self._thresholds.abstain_below or not result.evidence:
            return CategoryChoice.abstain(NO_EVIDENCE)
        return await self._ask(result, merchant, memo, direction)

    async def _ask(
        self, result: SearchResult, merchant: str, memo: str, direction: Direction
    ) -> CategoryChoice:
        prompt = classify_prompt(result, merchant, memo, direction)
        for _ in range(_ATTEMPTS):
            try:
                pick = parse_category_pick(await self._model.complete_json(prompt))
            except MalformedOutput:
                continue
            return _checked(pick, result)
        return CategoryChoice.abstain(NO_EVIDENCE)


def _checked(pick: CategoryPick, result: SearchResult) -> CategoryChoice:
    """받은 답을 7장 표의 순서대로 검사한다. 하나라도 걸리면 고르지 않는다."""
    allowed = {c.id for c in result.categories}
    given = {e.transaction_id for e in result.evidence}
    if pick.abstain or pick.category_id is None:
        return CategoryChoice.abstain(NO_EVIDENCE)
    if pick.category_id not in allowed:  # 없는 카테고리를 만들어 냈다
        return CategoryChoice.abstain(NO_EVIDENCE)
    if not set(pick.evidence_ids) <= given:  # 거래 id를 지어냈다
        return CategoryChoice.abstain(NO_EVIDENCE)
    if not pick.evidence_ids:  # 근거 없이 골랐다
        return CategoryChoice.abstain(NO_EVIDENCE)
    return CategoryChoice(pick.category_id, ChoiceStrategy.LLM, _clean_reason(pick.reason))


def _clean_reason(reason: str) -> str:
    """화면에 그대로 보일 한 문장. 둘 이상이면 자르고, 지시문이 섞였으면 버린다."""
    first = _FIRST_SENTENCE.split(reason.strip(), maxsplit=1)[0][:_REASON_LIMIT]
    return AI_PICKED if not first or _LEAKED.search(first) else first


def _similar(result: SearchResult) -> str:
    """`비슷한 기록: 메가커피 · 스타벅스 · 투썸플레이스 → 카페`"""
    top = result.candidates[0].category_id
    names: list[str] = []
    for e in result.evidence:
        if e.category_id == top and e.merchant not in names:
            names.append(e.merchant)
    return f"비슷한 기록: {' · '.join(names[:_SHOWN])} → {result.name_of(top)}"
