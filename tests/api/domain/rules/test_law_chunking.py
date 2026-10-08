from __future__ import annotations

from pathlib import Path

import pytest

from api.domain.entities import Document, DocumentChunk
from api.domain.rules.law_chunking import FIXED_SIZE, SPLIT_OVER, chunk_law, strip_tags
from api.domain.rules.law_markdown import parse_law
from api.domain.values import ChunkStrategy

LAWS = Path(__file__).parents[3] / "fixtures" / "ai" / "documents" / "laws"


def law(name: str) -> Document:
    return parse_law((LAWS / name).read_text(encoding="utf-8"))


def all_chunks(strategy: ChunkStrategy) -> list[DocumentChunk]:
    return [c for p in sorted(LAWS.glob("*.md")) for c in chunk_law(law(p.name), strategy)]


def test_tags_go_but_numbers_that_look_like_tags_stay():
    assert strip_tags("① 공제한다. <개정 2011.12.31, 2014.12.23>") == "① 공제한다."
    assert strip_tags("- 3. 삭제<2013.1.1>") == "- 3."
    assert strip_tags("[본조신설 1999.10.30][제목개정 2002.12.30]") == ""
    assert strip_tags("<16> 법 제126조의2제2항제3호다목") == "<16> 법 제126조의2제2항제3호다목"


def test_paragraph_is_one_chunk_per_clause_with_its_items():
    chunks = all_chunks(ChunkStrategy.PARAGRAPH)
    assert len(chunks) == 77  # scripts/fetch_laws.py --measure가 센 항 수
    second = next(c for c in chunks if c.id == "paragraph:조세특례제한법/제126조의2/2")
    assert second.heading == "제126조의2(신용카드 등 사용금액에 대한 소득공제) ②"
    assert "- 3. 다음 각 목에" in second.body and "  - 다. 대통령령으로" in second.body


def test_clause_sixteen_keeps_its_number_in_the_path_and_the_text():
    decree = chunk_law(law("tax-incentives-decree.md"), ChunkStrategy.PARAGRAPH)
    sixteen = next(c for c in decree if c.id == "paragraph:조세특례제한법 시행령/제121조의2/16")
    assert sixteen.search_text.startswith("<16> 법 제126조의2제2항제3호다목")


def test_body_is_the_original_and_only_search_text_drops_tags():
    for chunk in all_chunks(ChunkStrategy.PARAGRAPH):
        assert chunk.body in law_text(chunk.document_id)  # 원문의 한 조각 그대로
        assert "<개정" not in chunk.search_text and "[전문개정" not in chunk.search_text


def law_text(document_id: str) -> str:
    return next(
        p.read_text(encoding="utf-8")
        for p in LAWS.glob("*.md")
        if p.read_text(encoding="utf-8").startswith(f"# {document_id}\n")
    )


def test_paragraph_item_splits_long_clauses_and_adds_the_heads():
    chunks = chunk_law(law("tax-incentives-act.md"), ChunkStrategy.PARAGRAPH_ITEM)
    ids = [c.id.removeprefix("paragraph_item:조세특례제한법/제126조의2/") for c in chunks]
    assert ids[:4] == ["1", "2", "2/1", "2/2"]  # ①은 1,000자 아래라 통째로, ②는 머리와 호로
    item = next(c for c in chunks if c.id.endswith("/2/3"))
    assert item.heading == "제126조의2(신용카드 등 사용금액에 대한 소득공제) ② 3."
    assert item.body.startswith("- 3. 다음 각 목에") and "  - 가." in item.body
    title, head, rest = item.search_text.split("\n", 2)
    assert title.startswith("제126조의2(") and head.startswith("② 신용카드등소득공제금액은")
    assert rest.startswith("- 3. 다음 각 목에")
    whole = next(c for c in chunks if c.id.endswith("/1"))
    assert len(whole.body) <= SPLIT_OVER and whole.search_text.startswith("제126조의2(")


def test_fixed_windows_cover_the_body_without_overlap():
    tax = law("tax-incentives-act.md")
    chunks = chunk_law(tax, ChunkStrategy.FIXED_500)
    assert "".join(c.body for c in chunks) == tax.body
    assert all(len(c.body) <= FIXED_SIZE for c in chunks)
    assert chunks[0].id == "fixed_500:조세특례제한법/#1" and chunks[0].heading == "조세특례제한법"


@pytest.mark.parametrize("strategy", list(ChunkStrategy))
def test_same_law_same_chunks_unique_ids_and_ordered(strategy):
    chunks = all_chunks(strategy)
    assert chunks == all_chunks(strategy)
    assert len({c.id for c in chunks}) == len(chunks)
    tax = chunk_law(law("tax-incentives-act.md"), strategy)
    assert [c.position for c in tax] == list(range(1, len(tax) + 1))
    assert all(len(c.text_hash) == 16 for c in chunks)
