"""목록의 다음 쪽 커서. (occurred_at, id) 한 쌍을 불투명한 문자열로 싼다.

오프셋이 아니라 키셋이다 — 앞쪽에 거래가 끼어들어도 다음 쪽이 밀리거나 겹치지 않는다.
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime


def encode_cursor(occurred_at: datetime, transaction_id: str) -> str:
    raw = f"{occurred_at.isoformat()}|{transaction_id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str] | None:
    """못 읽는 커서는 None — 첫 쪽부터 다시 준다. 사람이 손으로 고친 URL에 500을 내지 않는다."""
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        moment, _, transaction_id = raw.partition("|")
        occurred_at = datetime.fromisoformat(moment)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    if occurred_at.tzinfo is None or not transaction_id:
        return None
    return occurred_at, transaction_id
