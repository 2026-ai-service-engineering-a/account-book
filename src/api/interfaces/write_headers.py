from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel

from .missing_idempotency_key import MissingIdempotencyKey


@dataclass(frozen=True, slots=True)
class WriteHeaders:
    """쓰기 요청의 머리글(api-contract 2·3·4장)."""

    idempotency_key: str
    confirmed: bool  # X-Confirmed-By: user — 사람이 눈으로 보고 눌렀다
    run_id: str | None  # X-Agent-Run-Id — 있으면 에이전트가 만든 기록이다

    def request_hash(self, method: str, path: str, body: BaseModel | None = None) -> str:
        """같은 키에 같은 요청인지 가린다. 키 순서가 달라도 같은 본문은 같은 해시다."""
        payload = [method, path, body.model_dump(mode="json") if body else None, self.run_id]
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()


def read_write_headers(
    idempotency_key: Annotated[str | None, Header(max_length=200)] = None,
    x_confirmed_by: Annotated[str | None, Header()] = None,
    x_agent_run_id: Annotated[str | None, Header(max_length=36)] = None,
) -> WriteHeaders:
    if not idempotency_key:
        raise MissingIdempotencyKey
    return WriteHeaders(idempotency_key, x_confirmed_by == "user", x_agent_run_id or None)


WriteHeadersDep = Annotated[WriteHeaders, Depends(read_write_headers)]
