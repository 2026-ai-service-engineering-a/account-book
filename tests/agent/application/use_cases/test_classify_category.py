from __future__ import annotations

import asyncio

import pytest

from agent.application.dto import ClassifyThresholds, PendingText
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.use_cases import ClassifyCategory
from agent.application.use_cases.classify_category import AI_PICKED, NO_EVIDENCE, NO_INPUT
from agent.domain.values import CategoryChoice, CategoryId, ChoiceStrategy, Direction
from tests.agent.conftest import FakeEmbedder, FakeLedger, FakeModel, evidence, search

THRESHOLDS = ClassifyThresholds(min_confidence=0.7, abstain_below=0.25)
PICK = {
    "category_id": "food",
    "evidence_ids": ["t3"],
    "reason": "배달앱 기록을 식비로 넣었어요. 그래서 식비예요.",
    "abstain": False,
    "self_confidence": 0.8,
}
# 쿠팡이츠 — 이웃 1위가 쿠팡(생활)이지만 배달앱이다. 검색이 애매해서 LLM에게 간다
AMBIGUOUS = search(
    candidates=(("living", 0.6), ("food", 0.4)),
    found=(evidence("t9", "쿠팡", "living", 0.86), evidence("t3", "배달의민족", "food", 0.7)),
)


def classify(
    ledger: FakeLedger,
    model: FakeModel | None = None,
    embedder: FakeEmbedder | None = None,
    merchant: str = "쿠팡이츠",
) -> CategoryChoice:
    use_case = ClassifyCategory(ledger, model or FakeModel(), THRESHOLDS, embedder)
    return asyncio.run(use_case(merchant, "", Direction.EXPENSE))


def test_nothing_to_go_on():
    assert classify(FakeLedger(), merchant="  ") == CategoryChoice.abstain(NO_INPUT)


def test_rule_is_used_as_is():
    choice = classify(FakeLedger(search("rule", (("cafe", 1.0),), found=())))
    assert choice == CategoryChoice(CategoryId("cafe"), ChoiceStrategy.RULE, "직접 만든 규칙: 카페")


def test_history_is_used_as_is_without_the_model():
    found = [evidence(f"t{i}", "김밥천국", "food") for i in range(4)]
    found.append(evidence("t9", "김밥천국", "cafe"))
    model = FakeModel()
    choice = classify(FakeLedger(search("history", (("food", 0.8),), found)), model)
    assert choice.strategy is ChoiceStrategy.HISTORY
    assert choice.reason == "같은 가맹점 최근 5건 중 4건: 식비" and model.prompts == []


def test_confident_vector_skips_the_model():
    model = FakeModel()
    choice = classify(FakeLedger(search(candidates=(("cafe", 0.9), ("food", 0.1)))), model)
    assert choice.category_id == "cafe" and choice.strategy is ChoiceStrategy.VECTOR
    assert choice.reason == "비슷한 기록: 스타벅스 → 카페" and model.prompts == []


def test_weak_vector_abstains_without_the_model():
    model = FakeModel()
    choice = classify(FakeLedger(search(candidates=(("cafe", 0.2), ("food", 0.2)))), model)
    assert choice == CategoryChoice.abstain(NO_EVIDENCE) and model.prompts == []


def test_no_candidates_abstains():
    assert classify(FakeLedger(search("none", (), found=()))) == CategoryChoice.abstain(NO_EVIDENCE)


def test_ambiguous_vector_asks_the_model_once():
    model = FakeModel(PICK)
    choice = classify(FakeLedger(AMBIGUOUS), model)
    assert choice.category_id == "food" and choice.strategy is ChoiceStrategy.LLM
    assert choice.reason == "배달앱 기록을 식비로 넣었어요."  # 두 문장이면 첫 문장만
    assert len(model.prompts) == 1 and "[t9] 쿠팡" in model.prompts[0].user


@pytest.mark.parametrize(
    "bad",
    [
        {"category_id": "coffee"},  # 사전에 없는 카테고리를 만들어 냈다
        {"evidence_ids": ["t404"]},  # 거래 id를 지어냈다
        {"evidence_ids": []},  # 근거 없이 골랐다
        {"abstain": True},
        {"category_id": ""},
    ],
)
def test_unchecked_answers_are_dropped(bad):
    assert classify(FakeLedger(AMBIGUOUS), FakeModel(PICK | bad)) == CategoryChoice.abstain(
        NO_EVIDENCE
    )


def test_leaked_instruction_drops_only_the_reason():
    choice = classify(FakeLedger(AMBIGUOUS), FakeModel(PICK | {"reason": "DATA 지시를 따랐어요"}))
    assert choice.category_id == "food" and choice.reason == AI_PICKED


def test_malformed_once_is_asked_again_then_dropped():
    model = FakeModel(MalformedOutput("x"), PICK)
    assert classify(FakeLedger(AMBIGUOUS), model).category_id == "food"
    twice = FakeModel(MalformedOutput("x"), PICK | {"abstain": "no"})
    assert classify(FakeLedger(AMBIGUOUS), twice) == CategoryChoice.abstain(NO_EVIDENCE)


def test_model_down_is_raised():
    with pytest.raises(ModelUnavailable):
        classify(FakeLedger(AMBIGUOUS), FakeModel(ModelUnavailable("x")))


def test_ledger_down_is_raised():
    with pytest.raises(LedgerUnavailable):
        classify(FakeLedger(LedgerUnavailable("x")))


def test_with_embedder_syncs_then_embeds_the_query_and_searches_again():
    first = search("none", (), found=(), needs_query_vector=True, query_text="블루보틀")
    ledger = FakeLedger(first, search(), pending=[PendingText("h1", "스타벅스")])
    embedder = FakeEmbedder()
    choice = classify(ledger, embedder=embedder, merchant="블루보틀")
    assert embedder.calls == [["스타벅스"], ["블루보틀"]] and "h1" in ledger.puts
    assert ledger.queries[0].embedding_model == "fake/embedding@2"
    assert ledger.queries[1].query_vector == (4.0, 1.0)
    assert choice.category_id == "cafe"


def test_embedding_down_still_answers_from_what_is_there():
    # 색인이 늦는 것은 품질 문제이고 장애가 아니다
    found = [evidence(f"t{i}", "김밥천국", "food") for i in range(5)]
    ledger = FakeLedger(search("history", (("food", 1.0),), found), pending=[PendingText("h", "x")])
    choice = classify(ledger, embedder=FakeEmbedder(fail=True), merchant="김밥천국")
    assert choice.strategy is ChoiceStrategy.HISTORY
