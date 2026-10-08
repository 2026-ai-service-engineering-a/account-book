"""채팅 답의 조문 출처 — search_documents가 낸 조각과 답이 붙인 ref(docs/ai/document-rag.md 5.5).

모델은 조각을 근거로 쓴 말 뒤에 `[d1a2b3c]`를 붙인다. 코드가 그 ref로 조각을 찾아 "[1]"로 바꾸고,
출처 줄(법령명·자리·시행일)을 붙인다. 출처는 모델이 쓰지 않는다 — 조 번호를 지어낼 길이 없다.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from agent.application.dto import ToolStep
from agent.domain.tools import ToolName

from .citation_check import source_text

_REF = r"d[0-9a-f]{6}"
_BARE = re.compile(rf"(?<![0-9A-Za-z]){_REF}(?![0-9A-Za-z])")
_GROUP = re.compile(rf"\[\s*{_REF}(?:\s*,\s*{_REF})*\s*\]")
_FOUND = 3  # 인용이 없을 때 보이는 찾은 조문 수

type Chunk = Mapping[str, object]


def documents_in(steps: Iterable[ToolStep]) -> dict[str, Chunk]:
    """성공한 search_documents가 낸 조각 — ref → 조각. 두 번 찾아 겹친 조각은 한 번."""
    found: dict[str, Chunk] = {}
    for step in steps:
        data = step.result.data
        if step.call.name != ToolName.SEARCH_DOCUMENTS.value or data is None:
            continue
        chunks = data.get("chunks")
        for chunk in chunks if isinstance(chunks, list) else []:
            if isinstance(chunk, Mapping) and isinstance(chunk.get("ref"), str):
                found.setdefault(str(chunk["ref"]), chunk)
    return found


def refs_in(text: str) -> list[str]:
    """답에 붙은 ref — 처음 나온 순서로, 겹치지 않게."""
    return list(dict.fromkeys(_BARE.findall(text)))


def without_refs(text: str) -> str:
    """숫자 검사용 — ref의 16진 숫자가 지어낸 숫자로 잡히지 않게."""
    return _BARE.sub("", text)


def sources(documents: Mapping[str, Chunk]) -> dict[str, str]:
    """인용 검증(citation_check)에 넘길 글."""
    return {
        ref: source_text(str(c.get("title", "")), str(c.get("heading", "")), str(c.get("body", "")))
        for ref, c in documents.items()
    }


def numbered(text: str, refs: list[str]) -> str:
    """`[d1a2b3c, d4e5f6a]` → `[1, 2]`. 괄호 밖에 홀로 쓴 ref도 `[n]`으로."""
    number = {ref: str(n) for n, ref in enumerate(refs, start=1)}

    def group(match: re.Match[str]) -> str:
        return "[" + ", ".join(number[r] for r in _BARE.findall(match.group())) + "]"

    text = _GROUP.sub(group, text)
    return _BARE.sub(lambda m: f"[{number[m.group()]}]", text)


def source_lines(refs: list[str], documents: Mapping[str, Chunk]) -> str:
    """인용한 조각의 출처. 인용이 없으면 빈 글."""
    if not refs:
        return ""
    lines = [f"[{n}] {_where(documents[ref])}" for n, ref in enumerate(refs, start=1)]
    return "\n".join(["출처", *lines])


def found_lines(documents: Mapping[str, Chunk]) -> str:
    """답이 조각을 인용하지 않았을 때 — 찾은 조문의 자리만. 원문은 문서 화면에서 본다."""
    if not documents:
        return ""
    lines = [f"- {_where(c)}" for c in list(documents.values())[:_FOUND]]
    return "\n".join(["찾은 조문", *lines])


def _where(chunk: Chunk) -> str:
    return f"{chunk.get('title')} {chunk.get('heading')} · 시행 {chunk.get('effective_date')}"
