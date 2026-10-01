from __future__ import annotations


class TransactionNotFound(Exception):
    """그 id의 거래가 없다. interfaces에서 404 not_found가 된다(development-rules 6.5)."""
