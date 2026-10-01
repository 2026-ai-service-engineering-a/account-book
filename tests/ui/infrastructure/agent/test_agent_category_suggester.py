from __future__ import annotations

import asyncio
import json

import httpx

from ui.application.dto import CategorySuggestion, Direction
from ui.application.values import CategoryId
from ui.infrastructure.agent import AgentCategorySuggester


def suggest(handler, merchant: str = "쿠팡이츠", memo: str = "") -> CategorySuggestion:
    suggester = AgentCategorySuggester(
        "http://agent", timeout=1, transport=httpx.MockTransport(handler)
    )
    return asyncio.run(suggester.suggest(merchant, memo, Direction.EXPENSE))


def test_posts_merchant_memo_direction_and_reads_the_choice():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = {"category_id": "food", "strategy": "llm", "reason": "배달앱이라 식비"}
        return httpx.Response(200, json=body)

    suggestion = suggest(handler, memo="야식")
    assert seen[0].url == "http://agent/classify"
    assert json.loads(seen[0].content) == {
        "merchant": "쿠팡이츠",
        "memo": "야식",
        "direction": "expense",
    }
    assert suggestion == CategorySuggestion(CategoryId("food"), "배달앱이라 식비", by_llm=True)


def test_agent_down_cannot_choose_but_says_so():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"code": "ledger_unavailable"}})

    suggestion = suggest(handler)
    assert suggestion.category_id is None and "직접 골라" in suggestion.reason
