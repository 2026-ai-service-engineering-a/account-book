from __future__ import annotations

from datetime import date
from typing import Protocol

from agent.application.dto import (
    CategoryQuery,
    DocumentQuery,
    PendingText,
    RetrievedChunk,
    SearchResult,
    TransactionFilter,
)
from agent.domain.tools import (
    BudgetLine,
    CategoryLine,
    CategoryShift,
    Frequency,
    SpendingTotals,
    TransactionList,
)
from agent.domain.values import CategoryId, TimeRange


class LedgerApi(Protocol):
    """agent가 보는 api. DB는 모른다 — 벡터 검색조차 이 엔드포인트를 지난다(docs/ai/README.md 3장).

    닿지 못하면 `LedgerUnavailable`, api가 에러 코드로 거절하면 그 하위형 `LedgerRejected`.
    집계는 api가 한다 — 여기서 받는 숫자는 전부 계산된 값이다(api-contract 6장).
    """

    async def suggest(self, query: CategoryQuery) -> SearchResult: ...

    async def pending(self, embedding_model: str, limit: int) -> tuple[PendingText, ...]: ...

    async def put_embedding(
        self, text_hash: str, embedding_model: str, vector: tuple[float, ...]
    ) -> None: ...

    async def transactions(self, where: TransactionFilter, limit: int) -> TransactionList: ...

    async def summary(self, where: TransactionFilter) -> SpendingTotals: ...

    async def frequency(self, where: TransactionFilter) -> Frequency: ...

    async def compare(
        self, a: TimeRange, b: TimeRange, category_id: CategoryId | None
    ) -> tuple[CategoryShift, ...]: ...

    async def budget_status(
        self, month: date, category_id: CategoryId | None
    ) -> tuple[BudgetLine, ...]:
        """`month`는 그 달 1일이다. 예산은 달 단위로만 있다."""
        ...

    async def categories(self) -> tuple[CategoryLine, ...]:
        """카테고리 사전 — 지출·수입 전부. 도구가 아니라 루프가 인자를 검사하는 데 쓴다."""
        ...

    async def search_documents(self, query: DocumentQuery) -> tuple[RetrievedChunk, ...]:
        """문서 조각 찾기 — 점수 높은 순으로 k개. 벡터를 실으면 api가 코사인·RRF로 찾는다."""
        ...
