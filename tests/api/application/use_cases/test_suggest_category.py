from __future__ import annotations

from api.application.dto import CategoryQuery, CategorySearch, SearchStrategy
from api.application.use_cases import CreateTransaction, SuggestCategory
from api.domain.rules.searchable_text import text_hash
from api.domain.values import CategoryId, Direction, Money
from tests.api.conftest import FakeUnitOfWork, draft

MODEL = "fake@2"
VECTORS = {"스타벅스": (1.0, 0.0), "김밥천국": (0.0, 1.0)}


def ledger() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    create = CreateTransaction(Money(10_000_000))
    for _ in range(5):
        create(uow, draft(merchant="김밥천국 강남점"), run_id=None, confirmed=True)
    create(uow, draft(merchant="스타벅스", category="cafe"), run_id=None, confirmed=True)
    create(
        uow,
        draft(merchant="월급", category="salary", direction=Direction.INCOME),
        run_id=None,
        confirmed=True,
    )
    return uow


def suggest(uow: FakeUnitOfWork, merchant: str, **kwargs) -> CategorySearch:
    return SuggestCategory(uow, top_k=8, temperature=0.03)(
        CategoryQuery(merchant, "", kwargs.pop("direction", Direction.EXPENSE), **kwargs)
    )


def test_rule_first():
    uow = ledger()
    uow.index.rules["김밥"] = CategoryId("cafe")
    found = suggest(uow, "김밥천국")
    assert found.strategy is SearchStrategy.RULE and found.candidates[0].category_id == "cafe"


def test_history_decides_a_regular_place_even_with_a_branch_suffix():
    found = suggest(ledger(), "김밥천국 역삼점")
    assert found.strategy is SearchStrategy.HISTORY and len(found.evidence) == 5
    assert found.query_text == "김밥천국"


def test_unknown_text_asks_for_a_query_vector_then_votes():
    uow = ledger()
    for text, vector in VECTORS.items():
        uow.index.put_embedding(MODEL, text_hash(text), vector)
    asked = suggest(uow, "블루보틀", embedding_model=MODEL)
    assert asked.strategy is SearchStrategy.NONE and asked.needs_query_vector
    found = suggest(uow, "블루보틀", embedding_model=MODEL, query_vector=(0.9, 0.1))
    assert found.strategy is SearchStrategy.VECTOR and found.candidates[0].category_id == "cafe"
    assert all(e.category_id != "salary" for e in found.evidence)  # 같은 방향만


def test_dictionary_of_the_direction_comes_along():
    found = suggest(ledger(), "월급", direction=Direction.INCOME)
    assert {c.id for c in found.categories} == {"salary"}
