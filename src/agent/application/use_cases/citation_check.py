"""조각을 인용한 답의 검증 — 문서 Q&A(/ask)와 채팅의 search_documents가 같이 쓴다.

인용은 넘겨준 이름 안에, 인용 없는 답은 근거가 없다고, 답의 숫자는 인용한 조각 안에
(docs/ai/document-rag.md 5.3). 채팅은 통계 도구의 숫자를 `allowed`로 더 넘긴다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set

from agent.application.dto import CitationVerdict

from .number_check import numbers_in, unsupported


def check_citations(
    answer: str,
    citations: Sequence[str],
    sources: Mapping[str, str],
    allowed: Set[str] = frozenset(),
) -> CitationVerdict:
    """`sources`는 인용 이름 → 그 조각의 글(법령명·자리·본문)."""
    if any(c not in sources for c in citations):
        return CitationVerdict.UNKNOWN
    if not citations:
        return CitationVerdict.MISSING
    cited = set(allowed).union(*(numbers_in(sources[c]) for c in citations))
    if unsupported(answer, cited):
        return CitationVerdict.NUMBERS
    return CitationVerdict.OK


def source_text(title: str, heading: str, body: str) -> str:
    """숫자를 볼 글 — 본문과 함께 자리("제8조 ① 1.")도. 조 번호를 말한 답이 버려지지 않게."""
    return f"{title} {heading}\n{body}"
