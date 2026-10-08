from __future__ import annotations

from dataclasses import dataclass

QUERY_LIMIT = 200  # api 문서 검색의 q 상한


@dataclass(frozen=True, slots=True)
class SearchDocumentsInput:
    query: str  # 찾을 내용 — 법령 조문을 묻는 한 문장

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query가 비었다 — 찾을 내용을 한 문장으로 적는다")
        if len(self.query) > QUERY_LIMIT:
            raise ValueError(f"query는 {QUERY_LIMIT}자까지다")
