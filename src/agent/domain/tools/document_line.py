from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

REF_PREFIX = "d"
_REF_HEX = 6


@dataclass(frozen=True, slots=True)
class DocumentLine:
    """search_documents가 낸 조문 조각 하나. 모델은 `ref`로 인용한다.

    ref는 조각 id에서 나온 짧은 이름이다(d + 16진 6자리). 긴 id를 옮겨 적다 틀리지 않게, 그리고
    한 대화에서 두 번 찾아도 같은 조각은 같은 이름이 되게 — 번호를 매기면 두 번째 찾기의 1번이
    첫 번째 찾기의 1번과 겹친다.
    """

    ref: str
    title: str  # 법령명
    heading: str  # 제19조 ① 같은 자리
    effective_date: date
    body: str

    @staticmethod
    def ref_for(chunk_id: str) -> str:
        digest = hashlib.sha256(chunk_id.encode()).hexdigest()
        return f"{REF_PREFIX}{digest[:_REF_HEX]}"
