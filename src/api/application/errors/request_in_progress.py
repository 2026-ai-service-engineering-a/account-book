from __future__ import annotations


class RequestInProgress(Exception):
    """같은 키의 요청이 아직 처리 중이다. 409 request_in_progress — 재시도하지 말고 기다린다."""
