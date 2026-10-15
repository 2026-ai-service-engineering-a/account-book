from __future__ import annotations

from dataclasses import dataclass

from .record_card import RecordCard


@dataclass(frozen=True, slots=True)
class RecordReply:
    """기록 자리의 답 하나 — 카드(제안), 글(기록했다·취소했다·거절), 또는 에러 코드.

    `wrote`는 api에 쓰기를 보냈다는 뜻이다 — 화면의 진행 줄("기록하는 중…")에 쓴다.
    """

    text: str = ""
    card: RecordCard | None = None
    code: str = ""  # 비어 있지 않으면 에러다
    wrote: bool = False
