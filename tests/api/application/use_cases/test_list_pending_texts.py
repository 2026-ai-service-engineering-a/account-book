from __future__ import annotations

from pathlib import Path

from api.application.use_cases import ListPendingTexts, LoadDocuments
from tests.api.application.use_cases.test_suggest_category import ledger

LAW = Path(__file__).parents[3] / "fixtures" / "ai" / "documents" / "laws" / "income-tax-act.md"


def test_unique_texts_without_a_vector_and_capped():
    uow = ledger()
    texts = sorted(p.text for p in ListPendingTexts(uow)("m", 100))
    assert texts == ["김밥천국", "스타벅스", "월급"]  # 김밥천국 다섯 건은 하나로
    assert len(ListPendingTexts(uow)("m", 10_000)) == 3


def test_document_chunks_fill_what_transactions_leave():
    uow = ledger()
    LoadDocuments(uow)([LAW.read_text(encoding="utf-8")])
    texts = ListPendingTexts(uow)("m", 200)
    assert [t.text for t in texts[:3]] == ["김밥천국", "스타벅스", "월급"]  # 거래가 먼저
    chunk_hashes = {c.text_hash for c in uow.documents.chunks.values()}
    assert {t.text_hash for t in texts[3:]} == chunk_hashes
    assert len(ListPendingTexts(uow)("m", 5)) == 5


def test_an_embedded_chunk_text_is_no_longer_pending():
    uow = ledger()
    LoadDocuments(uow)([LAW.read_text(encoding="utf-8")])
    first = ListPendingTexts(uow)("m", 200)[3]
    uow.index.put_embedding("m", first.text_hash, (0.0,))
    assert first.text_hash not in {t.text_hash for t in ListPendingTexts(uow)("m", 200)}
    assert first.text_hash in {t.text_hash for t in ListPendingTexts(uow)("other", 200)}
