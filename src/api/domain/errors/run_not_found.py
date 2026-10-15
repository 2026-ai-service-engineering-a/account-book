from __future__ import annotations


class RunNotFound(Exception):
    """그런 실행이 감사 로그에 없다. 404 not_found — 지난 제안을 다시 열려 한 것이다."""

    def __init__(self) -> None:
        super().__init__("not_found")
