from __future__ import annotations

from api.application.use_cases import ListPendingTexts
from tests.api.application.use_cases.test_suggest_category import ledger


def test_unique_texts_without_a_vector_and_capped():
    uow = ledger()
    texts = sorted(p.text for p in ListPendingTexts(uow)("m", 100))
    assert texts == ["김밥천국", "스타벅스", "월급"]  # 김밥천국 다섯 건은 하나로
    assert len(ListPendingTexts(uow)("m", 10_000)) == 3
