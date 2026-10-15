from __future__ import annotations

from dataclasses import dataclass

from mcp_server.domain.values import Direction, TimeRange


@dataclass(frozen=True, slots=True)
class LedgerFilter:
    """합계·건수를 셀 거래의 조건. 기간은 이미 경계로 풀렸다."""

    period: TimeRange
    category_id: str = ""
    text: str = ""  # 가맹점·메모 부분 일치
    direction: Direction | None = None
