"""거래를 색인 텍스트로 바꾸는 규칙(docs/ai/category-suggestion-rag.md 4.1).

`가맹점 + " " + 메모`이고, 같은 가게가 표기 때문에 남이 되지 않게 꼬리를 뗀다. 금액과 날짜는
넣지 않는다 — 임베딩은 숫자의 크기를 담지 못하고, 넣으면 검색 축만 흐려진다.
"""

from __future__ import annotations

import hashlib
import re

# "김밥천국 강남점", "투썸 2호점" — 띄어 쓴 지점명만 뗀다. "편의점"처럼 붙은 것은 이름이다.
_BRANCH = re.compile(r"\s+\S*점$")
_COMPANY = re.compile(r"\(주\)|㈜|주식회사")
_SPACES = re.compile(r"\s+")


def searchable_text(merchant: str, memo: str) -> str:
    name = _COMPANY.sub("", merchant).strip()
    name = _BRANCH.sub("", name)
    return _SPACES.sub(" ", f"{name} {memo}").strip()


def text_hash(text: str) -> str:
    """임베딩이 붙는 열쇠. 같은 텍스트는 같은 해시다 — 같은 가게 백 건이 벡터 하나를 나눠 쓴다."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]
