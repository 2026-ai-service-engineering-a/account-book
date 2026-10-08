"""법령 Markdown(scripts/fetch_laws.py가 쓴 모양)을 문서로 읽는다.

# 법령명
- 출처: …
- 법령일련번호(MST): …
- 시행일자: YYYY-MM-DD

## 제126조의2(제목)
…
"""

from __future__ import annotations

from datetime import date

from api.domain.entities import Document
from api.domain.values import DocumentId

_FIELDS = {
    "- 출처: ": "source",
    "- 법령일련번호(MST): ": "mst",
    "- 시행일자: ": "effective",
}


def parse_law(text: str) -> Document:
    """머리가 모자라면 ValueError — 출처·일련번호·시행일자 없는 법령은 답 아래에 붙일 게 없다."""
    lines = text.split("\n")
    if not lines[0].startswith("# "):
        raise ValueError("첫 줄은 '# 법령명'이다")
    title = lines[0].removeprefix("# ").strip()
    found: dict[str, str] = {}
    for line in lines[1:]:
        if line.startswith("## "):
            break
        for prefix, key in _FIELDS.items():
            if line.startswith(prefix):
                found[key] = line.removeprefix(prefix).strip()
    missing = sorted(set(_FIELDS.values()) - set(found))
    if missing:
        raise ValueError(f"{title}: 머리에 {', '.join(missing)}가 없다")
    start = text.find("\n## ")
    return Document(
        id=DocumentId(title),
        title=title,
        source=found["source"],
        mst=found["mst"],
        effective_date=date.fromisoformat(found["effective"]),
        body=text[start + 1 :].rstrip() + "\n" if start >= 0 else "",
    )
