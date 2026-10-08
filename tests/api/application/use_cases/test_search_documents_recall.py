"""문서 키워드 검색의 recall@5 — 정답 세트 시드로 청킹 전략 셋을 견준다(document-rag.md 6장).

실제 Postgres(pg_trgm)에 법령 아홉 조문을 넣고 잰다. 모델은 없다.

    make measure-docs      # 표를 찍는다. make dev로 db가 떠 있어야 한다

맞음: 위 다섯 조각 중 하나가 정답 단위(항·호·목)의 첫 30자를 원문(body)에 품는다. 고정 길이
조각에는 경로가 없어서, 세 전략에 같은 규칙을 쓰려고 글로 대조한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from api.application.use_cases import LoadDocuments, SearchDocuments
from api.domain.rules.law_chunking import chunk_law
from api.domain.rules.law_markdown import parse_law
from api.domain.values import ChunkStrategy
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parents[3] / "fixtures" / "ai"
LAWS = FIXTURES / "documents" / "laws"
K = 5
OPENING = 30


@dataclass(frozen=True)
class Graded:
    case: str
    rank: int | None  # 처음 맞은 순위(1부터). 못 찾았으면 None


def openings() -> dict[str, list[str]]:
    """질문 id → 정답 단위의 첫 30자들. 단위의 글은 항 단위 조각에서 찾는다."""
    clauses = {
        c.id.removeprefix("paragraph:"): c.body
        for p in sorted(LAWS.glob("*.md"))
        for c in chunk_law(parse_law(p.read_text(encoding="utf-8")), ChunkStrategy.PARAGRAPH)
    }
    found: dict[str, list[str]] = {}
    for case in json.loads((FIXTURES / "document_qa.json").read_text(encoding="utf-8"))["cases"]:
        units = []
        for e in case["evidence"]:
            text = clauses[f"{e['law']}/{e['article']}/{e['paragraph']}"]
            if "item" in e:
                text = next(b for b in text.split("\n- ") if b.startswith(f"{e['item']}."))
                text = "- " + text
            if "subitem" in e:
                text = next(
                    line
                    for line in text.split("\n")
                    if line.strip().startswith(f"- {e['subitem']}.")
                )
            units.append(text.strip()[:OPENING])
        if units:
            found[case["id"]] = units
    return found


def questions() -> dict[str, str]:
    cases = json.loads((FIXTURES / "document_qa.json").read_text(encoding="utf-8"))["cases"]
    return {c["id"]: c["question"] for c in cases}


def grade(search: SearchDocuments, strategy: ChunkStrategy) -> list[Graded]:
    asked, gold = questions(), openings()
    graded = []
    for case, units in gold.items():
        hits = search(asked[case], strategy, K)
        rank = next(
            (n for n, h in enumerate(hits, start=1) if any(u in h.chunk.body for u in units)), None
        )
        graded.append(Graded(case, rank))
    return graded


def test_recall_at_five_by_strategy(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    load = LoadDocuments(lambda: SqlUnitOfWork(sessions))
    load(p.read_text(encoding="utf-8") for p in sorted(LAWS.glob("*.md")))
    search = SearchDocuments(lambda: SqlUnitOfWork(sessions))
    print(f"\n== 키워드 검색(pg_trgm word_similarity) — 정답 세트 시드, k={K}")
    print(f"{'전략':16} {'recall@5':>9} {'MRR@5':>6}  맞은 질문")
    for strategy in ChunkStrategy:
        graded = grade(search, strategy)
        recall = sum(g.rank is not None for g in graded) / len(graded)
        mrr = sum(1 / g.rank for g in graded if g.rank) / len(graded)
        right = " ".join(f"{g.case}@{g.rank}" for g in graded if g.rank)
        print(f"{strategy.value:16} {recall:>9.2f} {mrr:>6.2f}  {right or '-'}")
        assert len(graded) == 30  # 답이 있거나 일부 있는 질문
