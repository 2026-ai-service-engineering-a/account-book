"""법령을 조각으로 나누는 셋(docs/ai/document-rag.md 7.2). 순수 함수다 — 같은 문서는 같은 조각이다.

- fixed_500: 구조를 모른 채 500자씩. 기준선이다.
- paragraph: 항 하나(딸린 호·목 포함)가 조각 하나.
- paragraph_item: 항이되, 1,000자가 넘으면 항 머리와 호마다 나눈다. 조각마다 조 제목을, 나눈 호에는
  항 머리까지 찾는 글 앞에 붙인다 — 호 하나만 떼어 놓으면 무엇에 관한 것인지 모른다(3.1).

`body`는 원문 그대로다. 개정 꼬리표는 `search_text`에서만 뺀다.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from api.domain.entities import Document, DocumentChunk
from api.domain.values import ChunkId, ChunkStrategy

from .searchable_text import text_hash

FIXED_SIZE = 500
SPLIT_OVER = 1_000  # paragraph_item이 호마다 나누는 항의 길이(글자)

# 개정 꼬리표 — <개정 2014.1.1>, <신설 …>, 삭제<2013.1.1>, [전문개정 …], [본조신설 …], [제목개정 …].
# 날짜가 있어야 꼬리표다. ⑮ 다음 항의 번호 <16>은 꼬리표처럼 생겼지만 지우면 안 된다.
TAG = re.compile(
    r"(?:삭제\s*)?<(?:개정|신설|삭제)?[^<>]*\d{4}\.[^<>]*>|\[(?:전문개정|본조신설|제목개정)[^\]]*\]"
)
_CLAUSE = re.compile(r"^(?:([①-⑮])|<(\d+)>)")
_ITEM = re.compile(r"^- (\d+(?:의\d+)?)\.")
_BLANKS = re.compile(r"[ \t]+")

# (항 번호와 표기, 항 머리 문단, 호 덩어리들). 항 번호가 없는 조는 (None, "", …)
type _Clause = tuple[tuple[int, str] | None, str, list[str]]


def strip_tags(text: str) -> str:
    """찾는 글 — 개정 꼬리표를 빼고, 빈칸을 하나로. 줄 구조는 둔다."""
    lines = (_BLANKS.sub(" ", TAG.sub("", line)).strip() for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def chunk_law(document: Document, strategy: ChunkStrategy) -> tuple[DocumentChunk, ...]:
    pieces = (
        _fixed(document)
        if strategy is ChunkStrategy.FIXED_500
        else _structured(document, strategy is ChunkStrategy.PARAGRAPH_ITEM)
    )
    return tuple(
        DocumentChunk(
            id=ChunkId(f"{strategy.value}:{path}"),
            document_id=document.id,
            strategy=strategy,
            heading=heading,
            body=body,
            search_text=search,
            text_hash=text_hash(search),
            position=n,
        )
        for n, (path, heading, body, search) in enumerate(pieces, start=1)
    )


type _Piece = tuple[str, str, str, str]  # (경로, heading, body, search_text)


def _fixed(document: Document) -> Iterator[_Piece]:
    text = document.body
    for n, start in enumerate(range(0, len(text), FIXED_SIZE), start=1):
        body = text[start : start + FIXED_SIZE]
        yield f"{document.id}/#{n}", document.title, body, strip_tags(body)


def _structured(document: Document, split: bool) -> Iterator[_Piece]:
    for article in document.body.split("\n## "):
        title, _, rest = article.removeprefix("## ").partition("\n")
        label = title.split("(", 1)[0]
        base = f"{document.id}/{label}"
        for number, head, items in _clauses(rest):
            path = f"{base}/{number[0]}" if number else base
            heading = f"{title} {number[1]}" if number else title
            block = "\n\n".join(filter(None, (head, "\n".join(items))))
            if not split:
                yield path, heading, block, strip_tags(block)
            elif len(block) <= SPLIT_OVER or not items:
                yield path, heading, block, strip_tags(f"{title}\n{block}")
            else:
                yield path, heading, head, strip_tags(f"{title}\n{head}")
                for item in items:
                    match = _ITEM.match(item)
                    mark = match.group(1) if match else "?"
                    yield (
                        f"{path}/{mark}",
                        f"{heading} {mark}.",
                        item,
                        strip_tags(f"{title}\n{head}\n{item}"),
                    )


def _clauses(text: str) -> list[_Clause]:
    """조 본문을 항으로. 호·목 목록은 바로 앞 항에 붙이고, 꼬리표만 있는 줄([전문개정 …])은 뺀다."""
    clauses: list[_Clause] = []
    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph or not TAG.sub("", paragraph).strip():
            continue
        if paragraph.startswith("- "):
            if not clauses:
                clauses.append((None, "", []))
            clauses[-1][2].extend(_items(paragraph))
            continue
        match = _CLAUSE.match(paragraph)
        number = None
        if match:
            circled, written = match.groups()
            value = ord(circled) - ord("①") + 1 if circled else int(written)
            number = (value, match.group(0))
        clauses.append((number, paragraph, []))
    return clauses


def _items(paragraph: str) -> list[str]:
    """목록 문단을 호 덩어리로 — 호 한 줄과 그 아래 목 줄들."""
    items: list[str] = []
    for line in paragraph.split("\n"):
        if line.startswith("- ") or not items:
            items.append(line)
        else:
            items[-1] += "\n" + line
    return items
