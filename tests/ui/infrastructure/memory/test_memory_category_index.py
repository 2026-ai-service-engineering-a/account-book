from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from tests.ui.conftest import SEOUL
from ui.application.dto import (
    CategoryQuery,
    CategorySearch,
    Direction,
    SearchStrategy,
    Source,
    Transaction,
)
from ui.application.values import AccountId, CategoryId, Money, TextHash
from ui.infrastructure.memory import MemoryCategoryIndex, MemoryStore
from ui.infrastructure.memory.searchable_text import text_hash

MODEL = "gemini/gemini-embedding-001"
# 2차원 가짜 임베딩. 카페끼리, 밥집끼리 가깝다
VECTORS = {
    "스타벅스": (1.0, 0.0),
    "메가커피": (0.95, 0.05),
    "김밥천국": (0.0, 1.0),
    "카페": (0.9, 0.1),
}


def add(store: MemoryStore, merchant: str, category: str, day: int, memo: str = "") -> None:
    direction = store.categories[CategoryId(category)].direction
    t = Transaction(
        id=store.next_id(),
        direction=direction,
        amount=Money(5000),
        occurred_at=datetime(2026, 9, day, 12, tzinfo=SEOUL),
        category_id=CategoryId(category),
        account_id=AccountId("card"),
        merchant=merchant,
        memo=memo,
        source=Source.MANUAL,
    )
    store.transactions[t.id] = t


@pytest.fixture
def store() -> MemoryStore:
    store = MemoryStore.create(SEOUL)
    for day in range(1, 6):
        add(store, "김밥천국", "food", day)
    add(store, "스타벅스", "cafe", 3)
    add(store, "스타벅스", "cafe", 9)
    add(store, "메가커피", "cafe", 4)
    add(store, "9월 급여", "salary", 10)
    return store


def index(store: MemoryStore) -> MemoryCategoryIndex:
    return MemoryCategoryIndex(store, top_k=8, temperature=0.03)


def search(store: MemoryStore, merchant: str, **kwargs) -> CategorySearch:
    query = CategoryQuery(merchant, "", kwargs.pop("direction", Direction.EXPENSE), **kwargs)
    return asyncio.run(index(store).suggest(query))


def embed_all(store: MemoryStore) -> None:
    for text, vector in VECTORS.items():
        store.embeddings[(MODEL, text_hash(text))] = vector


def test_rule_wins_first(store):
    store.rules["김밥"] = CategoryId("cafe")  # 사용자가 그렇게 정했다면 이력보다 앞선다
    found = search(store, "김밥천국 강남점")
    assert found.strategy is SearchStrategy.RULE and found.candidates[0].category_id == "cafe"


def test_history_decides_a_regular_place(store):
    found = search(store, "김밥천국 역삼점")
    assert found.strategy is SearchStrategy.HISTORY
    assert found.candidates[0].category_id == "food" and found.candidates[0].confidence == 1.0
    assert len(found.evidence) == 5 and found.evidence[0].occurred_at.day == 5  # 최근 것부터


def test_too_little_history_falls_through(store):
    # 스타벅스는 두 건뿐이다 — 5건 중 4건 규칙에 못 미친다
    assert search(store, "스타벅스").strategy is SearchStrategy.NONE


def test_unknown_text_asks_for_a_query_vector(store):
    embed_all(store)
    found = search(store, "블루보틀", embedding_model=MODEL)
    assert found.strategy is SearchStrategy.NONE and found.needs_query_vector
    assert found.query_text == "블루보틀"


def test_vector_votes_with_given_query_vector(store):
    embed_all(store)
    found = search(store, "블루보틀", embedding_model=MODEL, query_vector=(0.9, 0.1))
    assert found.strategy is SearchStrategy.VECTOR
    assert found.candidates[0].category_id == "cafe" and found.candidates[0].confidence > 0.9
    # 같은 텍스트는 이웃 하나 — 스타벅스 두 건이 표를 두 번 던지지 않는다. 대표는 최근 것
    merchants = [e.merchant for e in found.evidence]
    assert merchants.count("스타벅스") == 1
    starbucks = next(e for e in found.evidence if e.merchant == "스타벅스")
    assert starbucks.occurred_at.day == 9 and starbucks.similarity is not None


def test_stored_vector_of_the_query_text_is_reused(store):
    embed_all(store)  # "카페"는 이미 색인돼 있다
    found = search(store, "카페", embedding_model=MODEL)
    assert found.strategy is SearchStrategy.VECTOR and not found.needs_query_vector


def test_neighbours_only_from_the_same_direction(store):
    embed_all(store)
    store.embeddings[(MODEL, text_hash("9월 급여"))] = (0.9, 0.1)
    found = search(store, "블루보틀", embedding_model=MODEL, query_vector=(0.9, 0.1))
    assert all(e.category_id != "salary" for e in found.evidence)


def test_without_model_no_vector_step(store):
    embed_all(store)
    found = search(store, "블루보틀")
    assert found.strategy is SearchStrategy.NONE and not found.needs_query_vector


def test_returns_the_dictionary_of_the_direction(store):
    found = search(store, "월급", direction=Direction.INCOME)
    assert {c.id for c in found.categories} == {"salary", "other_income"}


def test_pending_is_unique_texts_without_a_vector(store):
    pending = asyncio.run(index(store).pending(MODEL, limit=50))
    assert sorted(p.text for p in pending) == ["9월 급여", "김밥천국", "메가커피", "스타벅스"]
    embed_all(store)
    assert [p.text for p in asyncio.run(index(store).pending(MODEL, limit=50))] == ["9월 급여"]


def test_another_model_means_everything_is_pending(store):
    embed_all(store)
    assert len(asyncio.run(index(store).pending("other/model", limit=50))) == 4


def test_put_embedding(store):
    asyncio.run(index(store).put_embedding(TextHash("h1"), MODEL, (0.1, 0.2)))
    assert store.embeddings[(MODEL, TextHash("h1"))] == (0.1, 0.2)
