from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import RunSeat, RunStatus


@dataclass(frozen=True, slots=True)
class RunQuery:
    """실행 목록의 조건 — 자리와 상태로 거르고 최신순으로 한 쪽씩(ui_docs/pages/runs.md)."""

    seat: RunSeat | None = None
    status: RunStatus | None = None
    cursor: str | None = None  # 앞 쪽의 마지막 줄. 못 읽으면 첫 쪽부터
    limit: int = 30
