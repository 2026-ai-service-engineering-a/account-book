"""문서 찾기 평가 — 청킹 셋, 방법 셋, k 셋의 recall@k와 MRR@k(docs/ai/document-rag.md 6·7.2).

실제 임베딩 모델과 떠 있는 api를 부른다. 생성 모델은 부르지 않는다. CI에서 돌지 않는다.

    make docs          # 조각을 넣어 둔다
    make eval-docs     # 처음 한 번은 색인 안 된 조각을 임베딩한다

질문마다 임베딩은 한 번이다 — 같은 벡터로 전략·방법을 바꿔 가며 묻는다. k=8로 한 번 묻고
앞 3·5·8개로 잰다. api의 하이브리드는 후보 수가 k와 무관해서 k=3의 결과가 k=8의 앞 셋이다.

맞음: 위 k개 중 하나가 정답 단위(항·호·목)의 첫 30자를 원문에 품는다 — api의 make measure-docs와
같은 규칙이다. 기본값은 고르지 않는다. 표까지만 낸다 — 사람이 표를 보고 고른다.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from agent.application.dto import DocumentQuery
from agent.application.use_cases import SyncIndex
from agent.domain.values import ChunkStrategy, SearchMode
from agent.infrastructure.http import HttpLedgerApi
from agent.infrastructure.llm import LitellmEmbedder
from agent.infrastructure.settings import Settings

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parents[3] / "fixtures" / "ai"
KS = (3, 5, 8)
OPENING = 30
_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def law_text(name: str) -> str:
    return next(
        text
        for p in sorted((FIXTURES / "documents" / "laws").glob("*.md"))
        if (text := p.read_text(encoding="utf-8")).startswith(f"# {name}\n")
    )


def opening(evidence: dict[str, object]) -> str:
    """정답 단위의 첫 30자 — 항이면 항 머리 문단, 호면 그 호 줄, 목이면 그 목 줄."""
    article = next(
        part
        for part in law_text(str(evidence["law"])).split("\n## ")[1:]
        if part.startswith(f"{evidence['article']}(")
    )
    number = int(str(evidence["paragraph"]))
    mark = _CIRCLED[number - 1] if number <= len(_CIRCLED) else f"<{number}>"
    blocks = article.split("\n\n")
    start = next(i for i, b in enumerate(blocks) if b.startswith(mark))
    unit = blocks[start]
    if "item" in evidence:
        items = blocks[start + 1].split("\n")
        unit = next(line for line in items if line.startswith(f"- {evidence['item']}."))
        if "subitem" in evidence:
            unit = next(
                line for line in items if line.strip().startswith(f"- {evidence['subitem']}.")
            )
    return unit.strip()[:OPENING]


def gold() -> list[tuple[str, str, list[str]]]:
    """(id, 질문, 정답 단위의 첫 30자들) — 답이 있거나 일부 있는 질문만."""
    cases = json.loads((FIXTURES / "document_qa.json").read_text(encoding="utf-8"))["cases"]
    return [
        (c["id"], c["question"], [opening(e) for e in c["evidence"]])
        for c in cases
        if c["evidence"]
    ]


def first_hit(bodies: list[str], units: list[str]) -> int | None:
    return next(
        (n for n, body in enumerate(bodies, start=1) if any(u in body for u in units)), None
    )


async def measure() -> dict[tuple[ChunkStrategy, SearchMode], list[int | None]]:
    settings = Settings()
    ledger = HttpLedgerApi(settings.api_base_url, timeout=60)
    embedder = LitellmEmbedder(
        settings.embedding_model,
        settings.api_key(settings.embedding_model),
        dimensions=settings.embedding_dimensions,
        timeout=60,
    )
    indexed = await SyncIndex(ledger, embedder).run()
    print(f"\n색인: 이번에 임베딩한 글 {indexed}개 · 모델 {embedder.model}")
    cases = gold()
    vectors = await embedder.embed([question for _, question, _ in cases])
    ranks: dict[tuple[ChunkStrategy, SearchMode], list[int | None]] = {}
    for strategy in ChunkStrategy:
        for mode in SearchMode:
            found: list[int | None] = []
            for (_, question, units), vector in zip(cases, vectors, strict=True):
                query = DocumentQuery(question, strategy, max(KS), mode)
                if mode is not SearchMode.KEYWORD:
                    query = DocumentQuery(question, strategy, max(KS), mode, embedder.model, vector)
                chunks = await ledger.search_documents(query)
                found.append(first_hit([c.body for c in chunks], units))
            ranks[(strategy, mode)] = found
    return ranks


def test_recall_and_mrr_by_strategy_mode_and_k():
    ranks = asyncio.run(measure())
    n = len(gold())
    head = " ".join(f"R@{k:<4}" for k in KS) + "  " + " ".join(f"MRR@{k:<2}" for k in KS)
    print(f"\n== 문서 찾기 — 정답 세트 시드 {n}건, 맞음 = 위 k개 안에 정답 단위의 첫 {OPENING}자")
    print(f"{'전략':15} {'방법':8} {head}")
    for (strategy, mode), found in ranks.items():
        recall = [sum(r is not None and r <= k for r in found) / n for k in KS]
        mrr = [sum(1 / r for r in found if r is not None and r <= k) / n for k in KS]
        cells = " ".join(f"{v:<6.2f}" for v in recall) + "  " + " ".join(f"{v:<6.2f}" for v in mrr)
        print(f"{strategy.value:15} {mode.value:8} {cells}")
    print("\n질문별 첫 정답 순위(k=8, -는 못 찾음)")
    ids = [case_id for case_id, _, _ in gold()]
    print(f"{'':24} " + " ".join(f"{i:>4}" for i in ids))
    for (strategy, mode), found in ranks.items():
        row = " ".join(f"{r if r else '-':>4}" for r in found)
        print(f"{strategy.value + ' ' + mode.value:24} {row}")
    assert len(ranks) == 9 and all(len(found) == n for found in ranks.values())
