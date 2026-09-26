from __future__ import annotations


class TransactionNotFound(Exception):
    """api의 `not_found`. 화면은 "그 거래를 찾지 못했어요"로 옮긴다."""
